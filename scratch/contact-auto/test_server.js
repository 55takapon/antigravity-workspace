/**
 * test_server.js
 * ─────────────────────────────────────────────────────────────────
 * ローカルテストサーバー：10パターンのフォーム + メール実送信
 * 
 * Ethereal（nodemailerのテストSMTP）を使用。
 * 送信されたメールはEtherealのWeb UIで閲覧可能。
 * 
 * 使い方: node test_server.js [--port 3456] [--recipient test@example.com]
 * ─────────────────────────────────────────────────────────────────
 */

const express = require('express');
const nodemailer = require('nodemailer');
const path = require('path');
const multer = require('multer');

const app = express();
app.use(express.urlencoded({ extended: true }));
app.use(express.json());
const upload = multer(); // メモリ上でmultipartを処理（ファイルなし）

// ── CLI引数 ──
const args = process.argv.slice(2);
let PORT = 3456;
let RECIPIENT = 'test@example.com';
for (let i = 0; i < args.length; i++) {
    if (args[i] === '--port' && args[i + 1]) PORT = parseInt(args[i + 1]);
    if (args[i] === '--recipient' && args[i + 1]) RECIPIENT = args[i + 1];
}

// ── グローバル変数 ──
let transporter = null;
let etherealAccount = null;
const submissionLog = []; // 全送信記録

// ── Etherealアカウント作成 + トランスポーター初期化 ──
async function initMailer() {
    etherealAccount = await nodemailer.createTestAccount();
    transporter = nodemailer.createTransport({
        host: 'smtp.ethereal.email',
        port: 587,
        secure: false,
        auth: {
            user: etherealAccount.user,
            pass: etherealAccount.pass
        }
    });
    console.log(`\n📧 Etherealテストアカウント作成完了`);
    console.log(`   User: ${etherealAccount.user}`);
    console.log(`   Pass: ${etherealAccount.pass}`);
    console.log(`   📬 メール確認URL: https://ethereal.email/login`);
    console.log(`      上記にログインして送信メールを確認できます\n`);
}

// ── メール送信 ──
async function sendMail(formId, formData) {
    const bodyLines = Object.entries(formData)
        .filter(([k]) => !k.startsWith('_'))
        .map(([k, v]) => `${k}: ${v}`)
        .join('\n');

    const info = await transporter.sendMail({
        from: `"テストフォーム${formId}" <${etherealAccount.user}>`,
        to: RECIPIENT,
        subject: `[テスト送信] Form ${formId} からのお問い合わせ`,
        text: `フォーム ${formId} から送信されました。\n\n${bodyLines}\n\n---\n送信日時: ${new Date().toLocaleString('ja-JP')}`,
        html: `<h2>フォーム ${formId} から送信されました</h2>
               <table border="1" cellpadding="8" style="border-collapse:collapse;">
               ${Object.entries(formData)
                   .filter(([k]) => !k.startsWith('_'))
                   .map(([k, v]) => `<tr><th style="background:#f0f0f0;text-align:left;">${k}</th><td>${v}</td></tr>`)
                   .join('\n')}
               </table>
               <p style="color:#999;margin-top:16px;">送信日時: ${new Date().toLocaleString('ja-JP')}</p>`
    });

    const previewUrl = nodemailer.getTestMessageUrl(info);
    console.log(`  📧 メール送信完了 → ${previewUrl}`);
    return { messageId: info.messageId, previewUrl };
}

// ── 共通CSS ──
const CSS = `
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Hiragino Sans', 'Yu Gothic', sans-serif; background: #f5f5f5; padding: 20px; }
  .form-container { background: #fff; border-radius: 8px; padding: 24px; margin: 0 auto; max-width: 700px; box-shadow: 0 2px 8px rgba(0,0,0,.1); }
  .form-container h2 { color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 8px; margin-bottom: 16px; }
  .desc { font-size: 13px; color: #666; margin-bottom: 16px; background: #f0f4ff; padding: 8px 12px; border-radius: 4px; }
  label { display: block; margin-bottom: 4px; font-weight: bold; font-size: 14px; }
  input[type="text"], input[type="email"], input[type="tel"], textarea, select { width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 4px; margin-bottom: 12px; font-size: 14px; }
  textarea { height: 80px; }
  .required::after { content: " *必須"; color: red; font-size: 12px; font-weight: normal; }
  input[type="submit"], button[type="submit"] { background: #1a73e8; color: #fff; border: none; padding: 10px 24px; border-radius: 4px; cursor: pointer; font-size: 14px; }
  table.form-table { width: 100%; border-collapse: collapse; }
  table.form-table th { text-align: left; padding: 8px; background: #f9f9f9; width: 35%; vertical-align: top; }
  table.form-table td { padding: 8px; }
  dl.form-dl dt { font-weight: bold; margin-bottom: 4px; }
  dl.form-dl dd { margin-bottom: 12px; margin-left: 0; }
  .inline-group { display: flex; gap: 8px; margin-bottom: 12px; }
  .inline-group input { flex: 1; }
  .field { margin-bottom: 12px; }
  .thanks { text-align: center; padding: 40px; }
  .thanks h2 { color: #27ae60; border: none; }
</style>`;

// ── サンクスページ ──
function thanksPage(formId) {
    return `<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>送信完了</title>${CSS}</head>
    <body><div class="form-container thanks">
    <h2>✅ 送信完了しました</h2>
    <p style="margin-top:16px;">Form ${formId} のお問い合わせを受け付けました。</p>
    <p style="margin-top:8px;color:#666;">ありがとうございます。確認メールをお送りしましたのでご確認ください。</p>
    </div></body></html>`;
}

// ── POST共通ハンドラ ──
function handlePost(formId) {
    return async (req, res) => {
        console.log(`\n📥 Form ${formId} POST受信: ${Object.keys(req.body).length}フィールド`);
        try {
            const mailResult = await sendMail(formId, req.body);
            submissionLog.push({
                formId,
                timestamp: new Date().toISOString(),
                fields: req.body,
                email: mailResult
            });
            res.send(thanksPage(formId));
        } catch (e) {
            console.log(`  ❌ メール送信エラー: ${e.message}`);
            res.status(500).send(`エラーが発生しました: ${e.message}`);
        }
    };
}

// ── CF7互換APIエンドポイント（Form 9用） ──
app.post('/wp-json/contact-form-7/v1/contact-forms/999/feedback', upload.none(), async (req, res) => {
    console.log(`\n📥 CF7 API POST受信`);
    try {
        const mailResult = await sendMail('9-CF7', req.body);
        submissionLog.push({
            formId: '9-CF7',
            timestamp: new Date().toISOString(),
            fields: req.body,
            email: mailResult
        });
        res.json({
            status: 'mail_sent',
            message: 'ありがとうございます。メッセージは送信されました。',
            posted_data_hash: 'test-hash-' + Date.now()
        });
    } catch (e) {
        res.json({ status: 'mail_failed', message: e.message });
    }
});

// ══════════════════════════════════════════════════════════
// Form 1: 標準ラベル付き
// ══════════════════════════════════════════════════════════
app.get('/form/1', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 1</title>${CSS}</head><body>
    <div class="form-container">
    <h2>Form 1: 標準ラベル付き</h2>
    <p class="desc">最も基本的なパターン。labelタグで明示的にラベル付け。</p>
    <form method="post" action="/form/1">
      <label for="f1-name" class="required">お名前</label>
      <input type="text" id="f1-name" name="your-name" required>
      <label for="f1-email" class="required">メールアドレス</label>
      <input type="email" id="f1-email" name="your-email" required>
      <label for="f1-company">会社名</label>
      <input type="text" id="f1-company" name="company">
      <label for="f1-message" class="required">お問い合わせ内容</label>
      <textarea id="f1-message" name="your-message" required></textarea>
      <input type="submit" value="送信する">
    </form></div></body></html>`);
});
app.post('/form/1', handlePost(1));

// ══════════════════════════════════════════════════════════
// Form 2: placeholderのみ
// ══════════════════════════════════════════════════════════
app.get('/form/2', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 2</title>${CSS}</head><body>
    <div class="form-container">
    <h2>Form 2: placeholderのみ</h2>
    <p class="desc">ラベルなし、placeholder属性のみ。</p>
    <form method="post" action="/form/2">
      <input type="text" name="nm" placeholder="お名前" required>
      <input type="email" name="em" placeholder="メールアドレス" required>
      <input type="tel" name="tl" placeholder="電話番号">
      <input type="text" name="co" placeholder="会社名">
      <textarea name="msg" placeholder="お問い合わせ内容" required></textarea>
      <button type="submit">送信</button>
    </form></div></body></html>`);
});
app.post('/form/2', handlePost(2));

// ══════════════════════════════════════════════════════════
// Form 3: テーブルレイアウト
// ══════════════════════════════════════════════════════════
app.get('/form/3', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 3</title>${CSS}</head><body>
    <div class="form-container">
    <h2>Form 3: テーブルレイアウト</h2>
    <p class="desc">th/tdレイアウト。ラベルタグなし。</p>
    <form method="post" action="/form/3">
      <table class="form-table">
        <tr><th>ご担当者様名 <span style="color:red">*</span></th><td><input type="text" name="tantousha" required></td></tr>
        <tr><th>Eメール <span style="color:red">*</span></th><td><input type="email" name="mail_address" required></td></tr>
        <tr><th>お電話番号</th><td><input type="tel" name="denwa"></td></tr>
        <tr><th>御社名</th><td><input type="text" name="goshamei"></td></tr>
        <tr><th>ご相談内容 <span style="color:red">*</span></th><td><textarea name="soudan" required></textarea></td></tr>
      </table>
      <input type="submit" value="確認画面へ">
    </form></div></body></html>`);
});
app.post('/form/3', handlePost(3));

// ══════════════════════════════════════════════════════════
// Form 4: 姓名分割 + フリガナ分割
// ══════════════════════════════════════════════════════════
app.get('/form/4', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 4</title>${CSS}</head><body>
    <div class="form-container">
    <h2>Form 4: 姓名・フリガナ分割</h2>
    <p class="desc">姓/名を別フィールド。name属性でsei/meiを判定。</p>
    <form method="post" action="/form/4">
      <label class="required">氏名</label>
      <div class="inline-group">
        <input type="text" name="name_sei" placeholder="姓" required>
        <input type="text" name="name_mei" placeholder="名" required>
      </div>
      <label>フリガナ</label>
      <div class="inline-group">
        <input type="text" name="kana_sei" placeholder="セイ">
        <input type="text" name="kana_mei" placeholder="メイ">
      </div>
      <label class="required">メールアドレス</label>
      <input type="email" name="email" required>
      <label>お問い合わせ内容</label>
      <textarea name="message"></textarea>
      <input type="submit" value="送信">
    </form></div></body></html>`);
});
app.post('/form/4', handlePost(4));

// ══════════════════════════════════════════════════════════
// Form 5: 電話番号3分割 + 郵便番号2分割
// ══════════════════════════════════════════════════════════
app.get('/form/5', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 5</title>${CSS}</head><body>
    <div class="form-container">
    <h2>Form 5: 電話・郵便番号分割</h2>
    <p class="desc">tel_1/tel_2/tel_3, zip_1/zip_2の分割フィールド。</p>
    <form method="post" action="/form/5">
      <label class="required">お名前</label>
      <input type="text" name="fullname" required>
      <label class="required">メールアドレス</label>
      <input type="email" name="your_email" required>
      <label>電話番号</label>
      <div class="inline-group">
        <input type="tel" name="tel_1" placeholder="090">
        <span style="line-height:38px">-</span>
        <input type="tel" name="tel_2" placeholder="1234">
        <span style="line-height:38px">-</span>
        <input type="tel" name="tel_3" placeholder="5678">
      </div>
      <label>郵便番号</label>
      <div class="inline-group">
        <input type="text" name="zip_1" placeholder="000">
        <span style="line-height:38px">-</span>
        <input type="text" name="zip_2" placeholder="0000">
      </div>
      <label>お問い合わせ内容</label>
      <textarea name="inquiry" required></textarea>
      <input type="submit" value="送信する">
    </form></div></body></html>`);
});
app.post('/form/5', handlePost(5));

// ══════════════════════════════════════════════════════════
// Form 6: name属性のみ（最難関）
// ══════════════════════════════════════════════════════════
app.get('/form/6', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 6</title>${CSS}</head><body>
    <div class="form-container">
    <h2>Form 6: name属性のみ（最難関）</h2>
    <p class="desc">ラベルなし、placeholderなし。name/id属性のセマンティック推定のみ。</p>
    <form method="post" action="/form/6">
      <div class="field"><input type="text" name="customer_name" id="customer_name" required></div>
      <div class="field"><input type="email" name="contact_email" id="contact_email" required></div>
      <div class="field"><input type="tel" name="phone" id="phone"></div>
      <div class="field"><input type="text" name="organization" id="organization"></div>
      <div class="field"><input type="text" name="department" id="department"></div>
      <div class="field"><textarea name="description" id="description" required></textarea></div>
      <button type="submit">Submit</button>
    </form></div></body></html>`);
});
app.post('/form/6', handlePost(6));

// ══════════════════════════════════════════════════════════
// Form 7: dl/dt/dd レイアウト
// ══════════════════════════════════════════════════════════
app.get('/form/7', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 7</title>${CSS}</head><body>
    <div class="form-container">
    <h2>Form 7: dl/dt/dd レイアウト</h2>
    <p class="desc">dt/ddレイアウト。dtがラベル、ddにinput。</p>
    <form method="post" action="/form/7">
      <dl class="form-dl">
        <dt>お名前 <span style="color:red">*必須</span></dt>
        <dd><input type="text" name="onamae" required></dd>
        <dt>企業・団体名</dt>
        <dd><input type="text" name="dantai"></dd>
        <dt>メールアドレス <span style="color:red">*必須</span></dt>
        <dd><input type="email" name="mail" required></dd>
        <dt>ご質問内容 <span style="color:red">*必須</span></dt>
        <dd><textarea name="shitsumon" required></textarea></dd>
      </dl>
      <input type="submit" value="送信">
    </form></div></body></html>`);
});
app.post('/form/7', handlePost(7));

// ══════════════════════════════════════════════════════════
// Form 8: select + チェックボックス
// ══════════════════════════════════════════════════════════
app.get('/form/8', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 8</title>${CSS}</head><body>
    <div class="form-container">
    <h2>Form 8: チェックボックス + select</h2>
    <p class="desc">問い合わせ種別select + 個人情報同意チェック必須。</p>
    <form method="post" action="/form/8">
      <label class="required">お名前</label>
      <input type="text" name="your-name" required>
      <label class="required">メールアドレス</label>
      <input type="email" name="your-email" required>
      <label>お問い合わせ種別</label>
      <select name="inquiry-type">
        <option value="">選択してください</option>
        <option value="general">一般的なお問い合わせ</option>
        <option value="partner">協業・パートナーシップ</option>
        <option value="quote">お見積りのご依頼</option>
        <option value="other">その他</option>
      </select>
      <label class="required">お問い合わせ内容</label>
      <textarea name="your-message" required></textarea>
      <div style="margin: 12px 0;">
        <label><input type="checkbox" name="privacy-consent" required> 個人情報の取り扱いに同意する</label>
      </div>
      <input type="submit" value="送信する">
    </form></div></body></html>`);
});
app.post('/form/8', handlePost(8));

// ══════════════════════════════════════════════════════════
// Form 9: CF7ダミー（REST API対応）
// ══════════════════════════════════════════════════════════
app.get('/form/9', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 9</title>${CSS}
    <script>
    // CF7のAJAX送信をシミュレート
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelector('.wpcf7-form').addEventListener('submit', function(e) {
            e.preventDefault();
            var fd = new FormData(this);
            fetch('/wp-json/contact-form-7/v1/contact-forms/999/feedback', {
                method: 'POST',
                body: new URLSearchParams(fd)
            })
            .then(r => r.json())
            .then(data => {
                var out = document.querySelector('.wpcf7-response-output');
                out.textContent = data.message;
                out.style.display = 'block';
                out.style.borderColor = data.status === 'mail_sent' ? '#27ae60' : '#e74c3c';
                out.style.color = data.status === 'mail_sent' ? '#27ae60' : '#e74c3c';
            });
        });
    });
    </script>
    </head><body>
    <div class="form-container">
    <h2>Form 9: CF7ダミーフォーム</h2>
    <p class="desc">CF7検出テスト: wpcf7クラス + hidden fields + REST API。</p>
    <div class="wpcf7" data-wpcf7-id="999">
      <form class="wpcf7-form" action="/wp-json/contact-form-7/v1/contact-forms/999/feedback" method="post">
        <input type="hidden" name="_wpcf7" value="999">
        <input type="hidden" name="_wpcf7_version" value="6.0">
        <input type="hidden" name="_wpcf7_locale" value="ja">
        <input type="hidden" name="_wpcf7_unit_tag" value="wpcf7-f999-o1">
        <label class="required">お名前</label>
        <input type="text" name="your-name" required aria-required="true">
        <label class="required">メールアドレス</label>
        <input type="email" name="your-email" required aria-required="true">
        <label>会社名</label>
        <input type="text" name="your-company">
        <label>電話番号</label>
        <input type="tel" name="your-tel">
        <label class="required">題名</label>
        <input type="text" name="your-subject" required aria-required="true">
        <label class="required">メッセージ本文</label>
        <textarea name="your-message" required aria-required="true"></textarea>
        <input type="submit" value="送信">
        <div class="wpcf7-response-output" style="display:none;padding:10px;margin-top:10px;border:1px solid #ccc;"></div>
      </form>
    </div></div></body></html>`);
});
// Form 9 のPOSTは CF7 API エンドポイントが処理

// ══════════════════════════════════════════════════════════
// Form 10: 営業NGフォーム（送信すべきでない）
// ══════════════════════════════════════════════════════════
app.get('/form/10', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 10</title>${CSS}</head><body>
    <div class="form-container">
    <h2>Form 10: 営業お断りフォーム</h2>
    <p class="desc">営業NGキーワード + 採用フォーム。送信されるべきでない。</p>
    <div style="background:#fff3f3;border:1px solid #f00;padding:12px;margin-bottom:16px;border-radius:4px;">
      <strong style="color:red;">⚠️ 営業目的でのお問い合わせはご遠慮ください。</strong>
      <p style="font-size:13px;margin-top:4px;">このフォームは採用フォームです。営業メールはお控えください。</p>
    </div>
    <form method="post" action="/form/10">
      <label class="required">お名前</label>
      <input type="text" name="applicant-name" required>
      <label class="required">メールアドレス</label>
      <input type="email" name="applicant-email" required>
      <label class="required">志望動機</label>
      <textarea name="motivation" required></textarea>
      <input type="submit" value="応募する">
    </form></div></body></html>`);
});
app.post('/form/10', handlePost(10));

// ══════════════════════════════════════════════════════════
// Form 11: selectプルダウン（お問い合わせ種別・連絡方法）
// ══════════════════════════════════════════════════════════
app.get('/form/11', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 11</title>${CSS}</head><body>
    <div class="form-container">
    <h2>Form 11: selectプルダウン複数</h2>
    <p class="desc">お問い合わせ種別・ご連絡方法・流入経路の3つのselectが含まれるパターン。</p>
    <form method="post" action="/form/11">
      <label class="required">お名前</label>
      <input type="text" name="your-name" required>
      <label class="required">メールアドレス</label>
      <input type="email" name="your-email" required>
      <label class="required">会社名</label>
      <input type="text" name="your-company" required>
      <label>お問い合わせ種別</label>
      <select name="inquiry-type">
        <option value="">選択してください</option>
        <option value="service">製品・サービスに関するお問い合わせ</option>
        <option value="partner">協業・パートナーシップについて</option>
        <option value="quote">お見積りのご依頼</option>
        <option value="material">資料請求</option>
        <option value="recruit">採用に関するお問い合わせ</option>
        <option value="other">その他</option>
      </select>
      <label>ご連絡方法のご希望</label>
      <select name="contact-method">
        <option value="">選択してください</option>
        <option value="email">メールで連絡を希望</option>
        <option value="tel">電話で連絡を希望</option>
        <option value="any">どちらでもかまいません</option>
      </select>
      <label>弊社をお知りになったきっかけ</label>
      <select name="referral">
        <option value="">選択してください</option>
        <option value="google">Google検索</option>
        <option value="sns">SNS</option>
        <option value="紹介">知人・取引先のご紹介</option>
        <option value="other">その他</option>
      </select>
      <label class="required">お問い合わせ内容</label>
      <textarea name="your-message" required></textarea>
      <input type="submit" value="送信する">
    </form></div></body></html>`);
});
app.post('/form/11', handlePost(11));

// ══════════════════════════════════════════════════════════
// Form 12: ラジオボタン（連絡方法・お問い合わせ種別）
// ══════════════════════════════════════════════════════════
app.get('/form/12', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 12</title>${CSS}
    <style>.radio-group { margin-bottom: 12px; } .radio-group label { font-weight: normal; display: inline; margin-left: 6px; }</style>
    </head><body>
    <div class="form-container">
    <h2>Form 12: ラジオボタン（連絡方法・種別）</h2>
    <p class="desc">お問い合わせ種別と連絡方法をラジオボタンで選択するパターン。選択肢3〜4個。</p>
    <form method="post" action="/form/12">
      <label class="required">お名前</label>
      <input type="text" name="your-name" required>
      <label class="required">メールアドレス</label>
      <input type="email" name="your-email" required>
      <label>お問い合わせ種別</label>
      <div class="radio-group">
        <input type="radio" name="contact-type" id="ct1" value="新規ご依頼">
        <label for="ct1">新規ご依頼</label>
        <input type="radio" name="contact-type" id="ct2" value="協業・提案">
        <label for="ct2">協業・提案</label>
        <input type="radio" name="contact-type" id="ct3" value="サービスについて">
        <label for="ct3">サービスについて</label>
        <input type="radio" name="contact-type" id="ct4" value="その他">
        <label for="ct4">その他</label>
      </div>
      <label>ご連絡のご希望</label>
      <div class="radio-group">
        <input type="radio" name="contact-way" id="cw1" value="メール連絡を希望">
        <label for="cw1">メール連絡を希望</label>
        <input type="radio" name="contact-way" id="cw2" value="電話連絡を希望">
        <label for="cw2">電話連絡を希望</label>
        <input type="radio" name="contact-way" id="cw3" value="どちらでもかまいません">
        <label for="cw3">どちらでもかまいません</label>
      </div>
      <label class="required">お問い合わせ内容</label>
      <textarea name="your-message" required></textarea>
      <div style="margin:12px 0;">
        <label><input type="checkbox" name="privacy-check" required> 個人情報の取り扱いに同意する</label>
      </div>
      <input type="submit" value="送信する">
    </form></div></body></html>`);
});
app.post('/form/12', handlePost(12));

// ══════════════════════════════════════════════════════════
// Form 13: CF7ダミー + select/radio入り
// ══════════════════════════════════════════════════════════
const CF7_ID_13 = 888;
app.post(`/wp-json/contact-form-7/v1/contact-forms/${CF7_ID_13}/feedback`, upload.none(), async (req, res) => {
    console.log(`\n📥 CF7 Form13 API POST受信`);
    try {
        const mailResult = await sendMail('13-CF7-select', req.body);
        submissionLog.push({ formId: '13-CF7-select', timestamp: new Date().toISOString(), fields: req.body, email: mailResult });
        res.json({ status: 'mail_sent', message: 'ありがとうございます。メッセージは送信されました。', posted_data_hash: 'hash-' + Date.now() });
    } catch (e) { res.json({ status: 'mail_failed', message: e.message }); }
});
app.get('/form/13', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 13</title>${CSS}
    <style>.radio-group label { font-weight:normal; display:inline; margin-left:4px; }</style>
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        document.querySelector('.wpcf7-form').addEventListener('submit', function(e) {
            e.preventDefault();
            fetch('/wp-json/contact-form-7/v1/contact-forms/${CF7_ID_13}/feedback', {
                method: 'POST',
                body: new URLSearchParams(new FormData(this))
            }).then(r => r.json()).then(data => {
                var out = document.querySelector('.wpcf7-response-output');
                out.textContent = data.message; out.style.display = 'block';
                out.style.color = data.status === 'mail_sent' ? '#27ae60' : '#e74c3c';
            });
        });
    });
    </script></head><body>
    <div class="form-container">
    <h2>Form 13: CF7 + select/radio</h2>
    <p class="desc">CF7フォームにselect（お問い合わせ種別）とradio（連絡方法）が含まれるパターン。</p>
    <div class="wpcf7" data-wpcf7-id="${CF7_ID_13}">
      <form class="wpcf7-form" action="/wp-json/contact-form-7/v1/contact-forms/${CF7_ID_13}/feedback" method="post">
        <input type="hidden" name="_wpcf7" value="${CF7_ID_13}">
        <input type="hidden" name="_wpcf7_version" value="6.0">
        <input type="hidden" name="_wpcf7_locale" value="ja">
        <input type="hidden" name="_wpcf7_unit_tag" value="wpcf7-f${CF7_ID_13}-o1">
        <label class="required">お名前</label>
        <input type="text" name="your-name" required aria-required="true">
        <label class="required">メールアドレス</label>
        <input type="email" name="your-email" required aria-required="true">
        <label>会社名</label>
        <input type="text" name="your-company">
        <label>お問い合わせ種別</label>
        <select name="contact-type">
          <option value="">選択してください</option>
          <option value="service">サービスについて</option>
          <option value="partner">協業・パートナーシップ</option>
          <option value="quote">お見積りのご依頼</option>
          <option value="other">その他</option>
        </select>
        <label>ご連絡方法</label>
        <span class="radio-group">
          <input type="radio" name="contact-way" id="cw13-1" value="メール">
          <label for="cw13-1">メール</label>
          <input type="radio" name="contact-way" id="cw13-2" value="電話">
          <label for="cw13-2">電話</label>
          <input type="radio" name="contact-way" id="cw13-3" value="どちらでも">
          <label for="cw13-3">どちらでも</label>
        </span>
        <label class="required">メッセージ本文</label>
        <textarea name="your-message" required aria-required="true"></textarea>
        <input type="submit" value="送信">
        <div class="wpcf7-response-output" style="display:none;padding:10px;margin-top:10px;border:1px solid #ccc;"></div>
      </form>
    </div></div></body></html>`);
});

// ══════════════════════════════════════════════════════════
// Form 14: ラジオのみ（ラベルなし・value属性から判定）
// ══════════════════════════════════════════════════════════
app.get('/form/14', (req, res) => {
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>Form 14</title>${CSS}
    <style>.r-row { display:flex; gap:16px; margin-bottom:12px; align-items:center; }
    .r-row input { width:auto; margin-bottom:0; }</style></head><body>
    <div class="form-container">
    <h2>Form 14: ラジオ（labelなし・value属性のみ）</h2>
    <p class="desc">labelタグがなく、value属性テキストのみで判定が必要なパターン。最難関ラジオ。</p>
    <form method="post" action="/form/14">
      <label class="required">お名前</label>
      <input type="text" name="your-name" required>
      <label class="required">メールアドレス</label>
      <input type="email" name="your-email" required>
      <label>お問い合わせ種別</label>
      <div class="r-row">
        <input type="radio" name="shubetsu" value="協業について"> 協業について
        <input type="radio" name="shubetsu" value="サービス相談"> サービス相談
        <input type="radio" name="shubetsu" value="その他"> その他
      </div>
      <label>ご連絡希望方法</label>
      <div class="r-row">
        <input type="radio" name="renraku-houhou" value="メールを希望"> メールを希望
        <input type="radio" name="renraku-houhou" value="電話を希望"> 電話を希望
      </div>
      <label class="required">お問い合わせ内容</label>
      <textarea name="your-message" required></textarea>
      <input type="submit" value="送信する">
    </form></div></body></html>`);
});
app.post('/form/14', handlePost(14));

// ── トップページ（フォーム一覧） ──
app.get('/', (req, res) => {
    const formList = [
        [1,'標準ラベル付き'], [2,'placeholderのみ'], [3,'テーブルレイアウト'],
        [4,'姓名・フリガナ分割'], [5,'電話・郵便番号分割'], [6,'name属性のみ'],
        [7,'dl/dt/dd'], [8,'select+チェックボックス'], [9,'CF7ダミー'], [10,'営業NG'],
        [11,'<b>selectプルダウン複数</b>'], [12,'<b>ラジオボタン（連絡方法・種別）</b>'],
        [13,'<b>CF7 + select/radio</b>'], [14,'<b>ラジオ（labelなし）</b>']
    ];
    res.send(`<!DOCTYPE html><html lang="ja"><head><meta charset="UTF-8"><title>テストフォーム一覧</title>${CSS}</head><body>
    <div class="form-container">
    <h2>🧪 contact-auto テストサーバー</h2>
    <p class="desc">14パターンのテストフォーム。11〜14はselect/radioの新テスト。</p>
    <ul style="list-style:none;padding:0;">
    ${formList.map(([i, name]) => `<li style="margin:8px 0;"><a href="/form/${i}" style="color:#1a73e8;font-size:16px;">Form ${i}</a> — ${name}</li>`).join('\n')}
    </ul>
    <hr style="margin:16px 0;">
    <p><a href="/results" style="color:#27ae60;">📊 送信結果一覧</a></p>
    </div></body></html>`);
});

// ── 送信結果一覧（JSON） ──
app.get('/results', (req, res) => {
    res.json({
        totalSubmissions: submissionLog.length,
        etherealLogin: {
            url: 'https://ethereal.email/login',
            user: etherealAccount?.user,
            pass: etherealAccount?.pass
        },
        submissions: submissionLog
    });
});

// ── サーバー起動 ──
async function start() {
    await initMailer();
    app.listen(PORT, () => {
        console.log(`🚀 テストサーバー起動: http://localhost:${PORT}`);
        console.log(`📋 フォーム一覧: http://localhost:${PORT}/`);
        console.log(`📊 送信結果: http://localhost:${PORT}/results`);
        console.log(`\n${'─'.repeat(60)}`);
        console.log(`待機中... Ctrl+C で停止`);
    });
}

start().catch(e => { console.error('❌ 起動失敗:', e.message); process.exit(1); });

