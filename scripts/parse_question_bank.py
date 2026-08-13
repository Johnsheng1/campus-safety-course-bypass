# -*- coding: utf-8 -*-
"""
解析安全教育课程题库 docx -> 结构化 JSON 答案映射库

用法:
    python parse_question_bank.py "输入.docx" "输出.json"

输出结构:
    {
      "入学安全": {
        "single": [["题干文本", "D"], ...],   # 单选/多选答案: A / A~B~C
        "multi":  [["题干文本", "A~C"], ...],
        "judge":  [["题干文本", "1"], ...]    # 判断题: 1=正确, 0=错误
      },
      ...
    }

关键解析规则:
- 章节标题: ^第[一二三四五六七八九十]+章
- 题型分区: （一）单选 / （二）多选 / （三）判断
- 答案位置: 题干末尾（D）或（AC）; 判断题用（A）=正确(1)/（B）=错误(0)
- 注意全角/半角括号、零宽字符、答案在开头 ( B )xxx 等变体
"""
import json
import re
import sys
import zipfile


def extract_docx_text(path):
    with zipfile.ZipFile(path) as z:
        xml = z.read('word/document.xml').decode('utf-8', errors='ignore')
    paras = re.findall(r'<w:p[ >].*?</w:p>', xml, re.DOTALL)
    return [''.join(re.findall(r'<w:t[^>]*>([^<]*)</w:t>', p)) for p in paras]


def norm_answer(a, sec):
    a = a.replace('​', '').replace('‍', '').replace(' ', '').strip()
    if sec == 'judge':
        if a in ('对', '正确', 'T', 'A'):
            return '1'
        if a in ('错', '错误', 'F', 'B'):
            return '0'
        return a
    seen = []
    for ch in a:
        if ch in 'ABCDEF' and ch not in seen:
            seen.append(ch)
    return '~'.join(seen)


def parse(lines):
    chapters = {}
    current_ch = None
    section = None
    qtype_map = {'单选': 'single', '多选': 'multi', '判断': 'judge'}
    ch_re = re.compile(r'^第[一二三四五六七八九十]+章\s*(\S.*)$')
    q_re = re.compile(r'^\s*\d+、(.*)$')

    cur_q = None
    cur_text = ''
    cur_opts = []

    def flush():
        nonlocal cur_q, cur_text, cur_opts
        if cur_q is not None and current_ch and section:
            chapters.setdefault(current_ch, {})
            chapters[current_ch].setdefault(section, [])
            chapters[current_ch][section].append([cur_text.strip(), cur_q])
        cur_q = None
        cur_text = ''
        cur_opts = []

    for raw in lines:
        s = raw.strip().replace('​', '').replace('‍', '')
        if not s:
            continue
        m = ch_re.match(s)
        if m and '…' not in s and len(s) < 20:
            flush()
            current_ch = m.group(1).strip()
            section = None
            continue
        if s.startswith('（一）') or s.startswith('（二）') or s.startswith('（三）'):
            flush()
            t = re.search(r'（[一二三]）(单选|多选|判断)题', s)
            if t:
                section = qtype_map[t.group(1)]
            continue
        if s.startswith('一、知识学习'):
            flush()
            section = None
            continue
        if s.startswith('二、章节测试'):
            continue
        if section:
            m = q_re.match(s)
            if m and not re.match(r'^\s*[A-F][\s、．.]', s):
                text = m.group(1).strip()
                ans = ''
                am = re.search(r'[（(]\s*([A-F]+|[对错])\s*[）)]\s*[。．]?\s*$', text)
                if am:
                    ans = norm_answer(am.group(1), section)
                    text = re.sub(r'[（(]\s*[A-F]+\s*[）)]\s*[。．]?\s*$', '', text).strip()
                else:
                    am2 = re.match(r'^\s*[（(]\s*([A-F])\s*[）)]\s*', text)
                    if am2:
                        ans = norm_answer(am2.group(1), section)
                        text = re.sub(r'^\s*[（(]\s*[A-F]\s*[）)]\s*', '', text).strip()
                flush()
                cur_q = ans
                cur_text = text
                continue
            if cur_q is not None and re.match(r'^\s*[A-F][\s、．.]', s):
                cur_opts.append(s)
                continue
    flush()
    return chapters


if __name__ == '__main__':
    in_path = sys.argv[1] if len(sys.argv) > 1 else r'C:\Users\johnsheng\Desktop\2026年课程内容（定稿版）.docx'
    out_path = sys.argv[2] if len(sys.argv) > 2 else r'C:\Users\johnsheng\AppData\Roaming\CherryStudio\Data\Skills\campus-safety-course\data\题库库.json'
    lines = extract_docx_text(in_path)
    bank = parse(lines)

    total = sum(len(q) for secs in bank.values() for q in secs.values())
    missing = [(ch, sec, q[:30]) for ch, secs in bank.items()
               for sec, qs in secs.items() for q, a in qs if not a]
    print(f'章节数: {len(bank)}, 总题目数: {total}, 缺答案: {len(missing)}')
    for m in missing:
        print('  缺:', m)

    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(bank, f, ensure_ascii=False, indent=2)
    print(f'已保存: {out_path}')
