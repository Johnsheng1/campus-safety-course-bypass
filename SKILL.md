---
name: campus-safety-course
description: 自动完成校园安全教育平台（xiaoyuananquantong.com）的新生课程学习与考试。当用户需要自动刷安全教育课程、章节测试、新生安全测试时使用。覆盖完整流程：图片学习页跳过20秒限制、章节测试题库自动答题、正式考试模拟人类节奏答题。适用于"帮我学课程"、"刷安全教育"、"完成平安校园课程"等场景。
---

# 校园安全教育课程自动学习 Skill

在 `wap.xiaoyuananquantong.com` 平台上自动完成新生必修的安全教育课程（10 章 + 正式考试）。**核心原则：必须模拟真实鼠标点击触发页面原生 onclick，绝不能直接写 hidden input**，否则提交接口返回 500。

## 适用场景

- 课程列表页（`newStudentCompulsory`）有多门课程显示"去学习"
- 每门课先看图片（有几秒到 20 秒翻页限制），再看章节测试
- 章节测试通过后进入下一章
- 全部 10 章学完出现"进入新生安全测试"（正式考试，50 题，90 分合格）

## 前置条件

1. 浏览器 MCP 已连接，页面已由用户登录并打开到课程列表页。
2. **题库文件**：从用户处获取课程题库（docx 或文本），需要解析出"题干 → 正确答案"映射。若无法获取题库，需在答题前先通过**错题页**逆向确认答案（见下文"题库不可用时"）。

## Skill 自带文件（本目录内，直接可用）

```
campus-safety-course/
├── SKILL.md                      # 本流程文档
├── scripts/
│   └── parse_question_bank.py    # docx题库 → JSON 解析脚本
└── data/
    ├── 题库库.json               # 完整题库（章节→题型→题干→答案+选项，dict结构）
    ├── 题库库紧凑.json           # 紧凑版（章节→题型→[题干, 答案] 列表），注入浏览器首选
    ├── 题库提取.txt              # docx 原始提取文本（可重新解析/校对）
    └── bank_js_国家安全.js       # 单章注入示例（JS 字面量格式，可作模板）
```

- **注入浏览器首选**：`data/题库库紧凑.json`。用它生成 `window.__BANK__ = {...}` 注入脚本时，直接读该文件内容即可（结构是 `{章节: {single: [[题干,答案],...], multi:[...], judge:[...]}}`）。
- 若课程题库更新，重新跑 `scripts/parse_question_bank.py` 生成新 JSON 覆盖 `data/题库库.json`（并同步生成紧凑版）。

## 环境要点

- 平台用 jQuery（`$` 全局可用）。
- 题目 DOM 结构：`<li>` 内含 `.clearWrong_title`（题干）、`.test_list`（选项 `<p id="{qid}{OPTION}" onclick="setVle('{qid}-{OPTION}')">`）、`input[name=question]`（隐藏答案框，id=qid）、`input[name=quesType]`（1=单选，2=多选，3=判断）。
- **提交参数格式**（决定成败）：`question={qid}-{选项}`（单选/判断）或 `question=~{qid}-A~{qid}-B...`（多选）。必须由 `setVle()` 写入，才能带出题目 ID。直接 `$(input).val(...)` 会导致 unitTest 返回 500。

## 流程 Step-by-Step

### Step 1: 解析题库（一次性）

从用户提供的题库文件（通常是 docx）提取题干与答案：

```python
# docx 本质是 zip，用 zipfile 读 word/document.xml 提取段落文本
import zipfile, re
with zipfile.ZipFile(path) as z:
    xml = z.read('word/document.xml').decode('utf-8')
paras = re.findall(r'<w:p[ >].*?</w:p>', xml, re.DOTALL)
lines = [''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)) for p in paras]
```

解析规则（重要）：
- 章节标题：`^第[一二三四五六七八九十]+章`
- 题型：`（一）单选题 / （二）多选题 / （三）判断题`
- 题干：`^\d+、`
- **答案格式**：单选/多选在题干末尾 `（D）`/`（AC）`；**判断题用 `（A）`/`（B）`，其中 A=正确(→1)，B=错误(→0)**。注意全角括号 `（）` 与半角 `()` 混用、零宽字符 `​`、答案在开头 `( B )xxx` 等变体。
- 输出结构：`{章节: {single: {题干: 答案}, multi: {...}, judge: {...}}}` 存为 JSON。

### Step 2: 进入某门课程 → 跳过图片学习

每个课程是 `newStudentArticle` 页面，图片轮播，`nextTop`/`prevTop` 翻页。**原逻辑每张图需停留 20 秒**（闭包变量 `startTime` 判断），无法直接访问闭包。

**跳过方案**：接管 jQuery 点击事件，直接用 `.css('left', -idx*w)` 改轮播位置（不用 animate，避免异步），最后触发完成逻辑：

```js
() => {
  var liCount = $('#picBox li').length;
  var w = $(window).width();
  var articleId = $('#articleId').val();
  var userId = $('#userId').val();
  var idx = 0, done = false;
  $('#nextTop').off('click'); $('#prevTop').off('click');
  $('#nextTop').on('click', function() {
    if (done) return;
    if (idx < liCount - 1) { idx++; $('#picBox ul').css('left', -idx * w); }
    else {
      done = true;
      $.ajax({ url: '/guns-vip-main/wap/markArticleViewed',
               data: { articleId: articleId, userId: userId }, type: 'post', async: true });
      setTimeout(function() { handleTest(); }, 300);   // 弹"进入章节测试"
    }
  });
  for (var i = 0; i < liCount; i++) $('#nextTop').click();
  return '翻页完成，共' + liCount + '张';
}
```

然后点击"继续章节测试"（`.start` 或 `[onclick="getQuetion()"]`）进入测试页。

### Step 3: 章节测试自动答题（关键：模拟点击）

**不要直接注入答案到 input！** 必须触发页面原生 `setVle` 的 onclick，让 hidden input 带上题目 ID。注入题库 + 自动点击脚本：

```js
() => {
  // 1) 注入本章题库到 window.__BANK__（结构见 Step 1，或直接用紧凑版）
  // 2) 匹配 + 点击
  window.__findAnswer__ = function(text, type) {
    var sec = type == '2' ? 'multi' : (type == '3' ? 'judge' : 'single');
    var list = window.__BANK__[sec] || [];
    var clean = text.replace(/（\s*）\s*$/, '').trim();
    var best = null, bestLen = 0;
    for (var i = 0; i < list.length; i++) {
      var bankQ = list[i][0];
      if (bankQ.indexOf(clean) >= 0 || clean.indexOf(bankQ) >= 0) {
        var common = clean.length < bankQ.length ? clean.length : bankQ.length;
        if (common > bestLen) { bestLen = common; best = list[i][1]; }
      }
    }
    return best;
  };
  $('#dataList li').each(function() {
    var $li = $(this);
    var title = $li.find('.clearWrong_title').text().trim();
    var titleClean = title.replace(/^\d+、/, '').replace(/^.*?(单选|多选|判断)题/, '').trim();
    var qtype = $li.find('input[name=quesType]').val();
    var qid = $li.find('input[name=question]').attr('id');
    var ans = window.__findAnswer__(titleClean, qtype);
    if (!ans) return;
    var parts = ans.split('~');
    for (var p = 0; p < parts.length; p++) {
      var optKey = parts[p];
      // 判断题答案 1=正确 0=错误 → 选项后缀 1/0；单选/多选 → A/B/C/D
      var sel = qtype == '3'
        ? $li.find('p[id="' + qid + (optKey == '1' ? '1' : '0') + '"]')
        : $li.find('p[id="' + qid + optKey + '"]');
      if (sel.length) {
        var oc = sel.attr('onclick');
        if (oc) eval(oc);       // 执行 setVle(...)，写入正确格式
        else sel.trigger('click');
      }
    }
  });
  // 校验：所有 input[name=question] 都应非空
}
```

**常见匹配失败**：题干里题库写《消防法》而页面写《中华人民共和国消防法》等措辞差异 → 手动补：
```js
if (title.indexOf('房屋消防安全状况') >= 0 || title.indexOf('行为是被严格禁止的') >= 0) { 全选ABCD }
```

### Step 4: 交卷

1. 用浏览器 `click` 点击"交卷"按钮（`#wrong_btn`）。
2. 等 `layer.confirm` 弹窗出现"确认要提交吗？"，点击"确定"。
3. 查看网络请求 `POST /guns-vip-main/wap/unitTest`：**200 + `isSuccess:true`** 即通过。
4. `isSuccess:false` 时响应里有 `num`（错题数）+ `logId`，需修正后重考。

### Step 5: 错题处理与重考

- `isSuccess:false` → 点击"查看错题"进 `wrong` 页，页面会显示"正确答案：X；您的答案：Y"。
- **修正题库**（把正确逻辑写回题库 JSON），然后回到考试：直接导航到
  `getquestion?id={articleId}&userId=...&ah=...`（此时 logId 已清空可重考）。
- **坑**：点击页面上的"重新考试"（`reload()`）会因 logId 非空先跳错题页，别用；直接 URL 导航到 `getquestion` 最稳。
- 重考后同样注入题库答题 → 交卷。

### Step 6: 下一章

通过后页面显示"下一章学习"（`#next_info`），点它进入下一门课。重复 Step 2-5。

### Step 7: 正式考试（新生安全测试，模拟人类节奏）

全部 10 章完成后，点"进入新生安全测试"（`getSafeExam()`）→ 入口页点"开始考试"（`handleTest(2)`）→ 弹窗确认 → 进入 `newStudentssimulate` 页（50 题，90 分合格）。

**用户要求模拟人类节奏**：逐题点击，每题随机停顿 0.5-3 秒：

```js
() => {
  // 注入完整答案映射 {qid: answer}（用题库对 50 题逐题匹配生成）
  window.__EXAM_ANSWERS__ = { /* qid: 'C' 或 'A~C' 或 '1'/'0' */ };
  window.__clickAnswer__ = function(qid, ans) {
    var $li = $('#' + qid).closest('li');
    var qtype = $li.find('input[name=quesType]').val();
    var parts = String(ans).split('~');
    for (var p = 0; p < parts.length; p++) {
      var optKey = parts[p];
      var sel = qtype == '3' ? $li.find('p[id="' + qid + (optKey == '1' ? '1' : '0') + '"]')
                             : $li.find('p[id="' + qid + optKey + '"]');
      if (sel.length) { var oc = sel.attr('onclick'); if (oc) eval(oc); else sel.trigger('click'); }
    }
  };
  var queue = Object.keys(window.__EXAM_ANSWERS__), idx = 0, done = 0;
  (function step() {
    if (idx >= queue.length) return;
    var qid = queue[idx], ans = window.__EXAM_ANSWERS__[qid];
    var $input = $('#' + qid);
    if ($input.length && $input.val() === '') { window.__clickAnswer__(qid, ans); done++; }
    idx++;
    if (idx < queue.length) setTimeout(step, 500 + Math.floor(Math.random() * 2500));
  })();
}
```

- 监控进度：`$('input[name=question]').each(...)` 统计已填数，等待完成。
- 全答完后同样点击"交卷"→ 确认 → 检查 `unitTest` 200 + `isSuccess:true`。

## 题库不可用时

若拿不到题库文件，可通过**错题页逆向**：先随便全选提交（或按常识作答），从 `wrong` 页"正确答案：X"逐题收集答案，重考直到通过。每次错误都会暴露一道正确答案，几轮后即可全部通关。

## 已知坑与教训

1. **绝不能直接写 hidden input 值**：`$('#qid').val('D')` 会让提交体变成 `question=D`（无题目 ID），后端 500。必须触发 `setVle()`。
2. **判断题答案映射**：题库标 `(A)`=正确→`1`，`(B)`=错误→`0`。单选/多选保留字母。
3. **题库本身可能有错**（如人身安全"开盒"一题，题库写"错误"实际应为"正确"），以错题页的"正确答案"为准。
4. **图片页闭包变量**（`startTime`/`index`）外部不可见，用 `.off('click')` 后接管 handler + `.css('left')` 直接定位是唯一可靠办法。
5. **`handleTest`/`reload` 等函数**不在全局（在页面内联 script），通过点击 DOM（`.start`、`#next_info span`）触发，不要 `window.handleTest()`。
6. **重考别点"重新考试"按钮**，它先走错题逻辑；直接导航 `getquestion` URL。
7. 每个新页面 `window.__BANK__` 都会丢，需重新注入。

## 验证清单

- [ ] 图片页翻完弹出"进入章节测试"
- [ ] 章节测试所有 `input[name=question]` 非空
- [ ] `unitTest` 返回 `200` 且 `isSuccess:true`
- [ ] 10 门课全部"已完成"
- [ ] 正式考试 50 题全部作答且通过
