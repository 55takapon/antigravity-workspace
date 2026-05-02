/**
 * daily-report-collector.js v2.0
 * 本日の全セッションから以下を抽出する：
 *   1. ユーザーの指摘・トラブル（怒りワード検出）
 *   2. 主要作業（USER_REQUESTの内容）
 *
 * ⚠️ このスクリプトは「補助ツール」。
 *    「全作業の網羅確認」はスクリプトだけで完結しない。
 *    出力を見た上で、必要に応じてoverview.txtを目視確認すること。
 */
const fs = require('fs');
const path = require('path');

const BRAIN_DIR = path.join(__dirname, '..', '..', '..', '..', 'brain');
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

function analyzeSession(sessionId) {
  const overviewPath = path.join(BRAIN_DIR, sessionId, '.system_generated', 'logs', 'overview.txt');
  const content = fs.readFileSync(overviewPath, 'utf-8');
  const lines = content.split('\n');

  const incidents = [];
  const requests = [];

  const angerWords = [
    'デタラメ', '出来損ない', 'ダメ', 'なんで', '勝手に', '指示以外',
    '上書き', '編集削除', '無責任', '信用に値しない', '却下', '適当',
    'やり直し', 'ゴミ', 'チンタラ', 'めちゃくちゃ', '間違え', 'テキトー',
    '漏らす', '虚偽', '嘘'
  ];

  for (const line of lines) {
    if (!line.includes('"USER_INPUT"')) continue;

    let obj;
    try { obj = JSON.parse(line); } catch(e) { continue; }

    const text = obj.content || '';

    // USER_REQUESTタグの内容を抽出
    const reqMatch = text.match(/<USER_REQUEST>\s*([\s\S]*?)\s*<\/USER_REQUEST>/);
    const userText = reqMatch
      ? reqMatch[1].replace(/\\n/g, '\n').trim()
      : text.replace(/<[^>]+>/g, '').trim().substring(0, 200);

    if (!userText) continue;

    // 全リクエストを記録（作業の網羅確認用）
    requests.push({
      step: obj.step_index,
      text: userText.substring(0, 120)
    });

    // 怒りワード検出
    const found = angerWords.filter(w => text.includes(w));
    if (found.length > 0) {
      incidents.push({
        step: obj.step_index,
        time: obj.created_at,
        keywords: found,
        text: userText.substring(0, 300)
      });
    }
  }

  return { incidents, requests };
}

function main() {
  const sessions = findTodaySessions();

  console.log(`\n===== Daily Report Collector v2.0 =====`);
  console.log(`対象日: ${todayStr}`);
  console.log(`検出セッション数: ${sessions.length}\n`);

  let allIncidents = [];

  for (const sessionId of sessions) {
    const result = analyzeSession(sessionId);
    console.log(`📁 ${sessionId.substring(0, 8)}...`);
    console.log(`   ユーザーリクエスト数: ${result.requests.length}`);
    console.log(`   🚨 指摘/トラブル: ${result.incidents.length}件`);

    // 全リクエストを表示（作業網羅確認用）
    if (result.requests.length > 0) {
      console.log(`   📋 リクエスト一覧（DONEに漏れがないか確認）:`);
      result.requests.forEach(r => {
        console.log(`     [step ${r.step}] ${r.text.substring(0, 80).replace(/\n/g, ' ')}`);
      });
    }

    // インシデント詳細
    for (const inc of result.incidents) {
      console.log(`   ⚡ INCIDENT [step ${inc.step}] KW: ${inc.keywords.join(', ')}`);
      console.log(`       → ${inc.text.substring(0, 80).replace(/\n/g, ' ')}`);
      allIncidents.push({ sessionId, ...inc });
    }
    console.log('');
  }

  console.log(`\n===== サマリー =====`);
  console.log(`全セッション: ${sessions.length}`);
  console.log(`指摘/トラブル総数: ${allIncidents.length}`);
  console.log(`\n⚠️  上記リクエスト一覧を元に、レポートのDONEセクションに漏れがないか確認すること。`);
  console.log(`⚠️  このスクリプトは補助ツール。怒りワードなしの重要作業は目視確認が必要。`);

  if (allIncidents.length > 0) {
    console.log(`\n🔴 以下のインシデントがレポートのINCIDENTに含まれているか確認:`);
    for (const inc of allIncidents) {
      console.log(`  - [${inc.sessionId.substring(0,8)}] ${inc.keywords.join(', ')}: ${inc.text.substring(0, 60).replace(/\n/g, ' ')}...`);
    }
  }
}

main();
