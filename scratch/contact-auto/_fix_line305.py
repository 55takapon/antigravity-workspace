import sys

file_path = r'c:\Users\hangy\.gemini\antigravity\scratch\contact-auto\contact_auto.js'
with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Total lines before: {len(lines)}')

# 壊れている304行目(0-indexed)を置換
new_lines = [
    "    console.log('');\n",
    "    for (const line of summary) {\n",
    "        console.log('  ' + line);\n",
    "    }\n",
    "    console.log('');\n",
    "\n",
    "    // -- skill_learner: 日次スキル自動学習 --\n",
    "    if (!dryRun) {\n",
    "        console.log('\\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');\n",
    "        console.log('日次スキル自動学習 (skill_learner) を起動...');\n",
    "        try {\n",
    "            const { execSync } = require('child_process');\n",
    "            const learnerPath = path.join(__dirname, 'skill_learner.js');\n",
    "            execSync('node ' + JSON.stringify(learnerPath) + ' --min-count 1', {\n",
    "                cwd: __dirname,\n",
    "                stdio: 'inherit',\n",
    "                timeout: 30000\n",
    "            });\n",
    "        } catch (e) {\n",
    "            console.log('  skill_learner 実行エラー（スキップ）: ' + (e.message || '').substring(0, 80));\n",
    "        }\n",
    "    }\n",
    "}\n",
]

lines[304] = ''.join(new_lines)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(lines)

with open(file_path, 'r', encoding='utf-8') as f:
    final_lines = f.readlines()
print(f'Total lines after: {len(final_lines)}')
print('Done.')
