/**
 * daily-report-collector.js
 * デイリーレポート作成前に実行し、本日の全セッションから
 * ユーザーの指摘・トラブル・主要作業を自動抽出するスクリプト
 */
const fs = require('fs');
const path = require('path');

const BRAIN_DIR = path.join(__dirname, '..', '..', '..', 'brain');
const today = new Date();
const todayStr = today.toISOString().split('T')[0]; // YYYY-MM-DD

function findTodaySessions() {
  const dirs = fs.readdirSync(BRAIN_DIR).filter(d => {
    const overviewPath = path.join(BRAIN_DIR, d, '.system_generated', 'logs', 'overview.txt');
    if (!fs.existsSync(overviewPath)) return false;
    const stat = fs.statSync(overviewPath);
    return stat.mtime >= new Date(todayStr + 'T00:00:00');
  });
  return dirs;
}

function extractUserInputs(sessionId) {
  const overviewPath = path.join(BRAIN_DIR, sessionId, '.system_generated', 'logs', 'overview.txt');
  const content = fs.readFileSync(overviewPath, 'utf-8');
  const lines = content.split('\n');
  
  const inputs = [];
  const incidents = [];
  
  for (const line of lines) {
    if (!line.includes('"USER_INPUT"')) continue;
    
    try {
      const obj = JSON.parse(line);
      const text = obj.content || '';
      
      // ユーザーの指摘・怒りワードを検出
      const angerWords = ['デタラメ', '出来損ない', 'ダメ', 'なんで', '勝手に', '指示以外', 
                          '上書き', '編集削除', '無責任', '信用に値しない', '却下', '適当',
                          'やり直し', 'ゴミ', 'チンタラ', 'めちゃくちゃ'];
      
      const found = angerWords.filter(w => text.includes(w));
      if (found.length > 0) {
        // USER_REQUESTタグ内のテキストだけ抽出
        const match = text.match(/<USER_REQUEST>\s*\\n([\s\S]*?)\\n<\/USER_REQUEST>/);
        const userText = match ? match[1].replace(/\\n/g, '\n').trim() : text.substring(0, 200);
        incidents.push({
          step: obj.step_index,
          time: obj.created_at,
          keywords: found,
          text: userText.substring(0, 300)
        });
      }
      
      inputs.push({
        step: obj.step_index,
        time: obj.created_at,
        text: text.substring(0, 150)
      });
    } catch(e) {
      // JSON parse error - skip
    }
  }
  
  return { totalInputs: inputs.length, incidents };
}

function main() {
  const sessions = findTodaySessions();
  
  console.log(`\n===== Daily Report Collector =====`);
  console.log(`対象日: ${todayStr}`);
  console.log(`検出セッション数: ${sessions.length}\n`);
  
  let allIncidents = [];
  
  for (const sessionId of sessions) {
    const result = extractUserInputs(sessionId);
    console.log(`📁 ${sessionId}`);
    console.log(`   ユーザー入力数: ${result.totalInputs}`);
    console.log(`   🚨 指摘/トラブル検出: ${result.incidents.length}件`);
    
    for (const inc of result.incidents) {
      console.log(`     [step ${inc.step}] ${inc.time}`);
      console.log(`       キーワード: ${inc.keywords.join(', ')}`);
      console.log(`       内容: ${inc.text.substring(0, 100)}...`);
      allIncidents.push({ sessionId, ...inc });
    }
    console.log('');
  }
  
  console.log(`\n===== サマリー =====`);
  console.log(`全セッション: ${sessions.length}`);
  console.log(`指摘/トラブル総数: ${allIncidents.length}`);
  
  if (allIncidents.length > 0) {
    console.log(`\n⚠️ 以下の指摘がレポートのINCIDENTに含まれているか必ず確認:`);
    for (const inc of allIncidents) {
      console.log(`  - [${inc.sessionId.substring(0,8)}] ${inc.keywords.join(', ')}: ${inc.text.substring(0, 80)}...`);
    }
  }
}

main();
