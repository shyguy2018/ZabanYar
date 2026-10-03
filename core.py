# -*- coding: utf-8 -*-
"""
Core logic (platform independent): keyboard-layout mapping + decision whether
a typed word was written in the wrong layout (English <-> Persian).
"""
import math
import re
import os
import sys

# ---------------------------------------------------------------- mapping ---
# Fallback static map (US key -> Persian char). On Windows the app asks the OS
# for the exact char of the user's own Persian layout, so this is only a backup.
EN2FA = {
    'q': 'ض', 'w': 'ص', 'e': 'ث', 'r': 'ق', 't': 'ف', 'y': 'غ', 'u': 'ع',
    'i': 'ه', 'o': 'خ', 'p': 'ح', '[': 'ج', ']': 'چ', 'a': 'ش', 's': 'س',
    'd': 'ی', 'f': 'ب', 'g': 'ل', 'h': 'ا', 'j': 'ت', 'k': 'ن', 'l': 'م',
    ';': 'ک', "'": 'گ', 'z': 'ظ', 'x': 'ط', 'c': 'ز', 'v': 'ر', 'b': 'ذ',
    'n': 'د', 'm': 'پ', ',': 'و', '\\': 'پ', '`': 'پ',
    'H': 'آ', 'C': 'ژ', 'M': 'ء',
    '1': '۱', '2': '۲', '3': '۳', '4': '۴', '5': '۵',
    '6': '۶', '7': '۷', '8': '۸', '9': '۹', '0': '۰', '?': '؟',
}
FA2EN = {}
for _k, _v in EN2FA.items():
    FA2EN.setdefault(_v, _k)
FA2EN.update({'پ': 'm', 'ئ': 'm', 'ي': 'd', 'ك': ';', 'ـ': 'j'})

PERSIAN_CHARS = set('ابپتثجچحخدذرزژسشصضطظعغفقکگلمنوهیآءئأؤإةيك‌')


def en_to_fa(s):
    out = []
    for ch in s:
        if ch in EN2FA:
            out.append(EN2FA[ch])
        elif ch.isalpha() and ch.lower() in EN2FA:      # caps-lock / shift
            out.append(EN2FA[ch.lower()])
        else:
            out.append(ch)
    return ''.join(out)


def fa_to_en(s):
    return ''.join(FA2EN.get(ch, ch) for ch in s)


def normalize_fa(s):
    return s.replace('ي', 'ی').replace('ك', 'ک').replace('ى', 'ی')


# ------------------------------------------------------------- dictionary ---
def _resource_dir():
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, 'data')


class Lexicon:
    def __init__(self, path):
        self.freq = {}
        self.bigram = {}
        counts, totals = {}, {}
        with open(path, encoding='utf-8') as f:
            for line in f:
                line = line.rstrip('\n')
                if not line:
                    continue
                w, z = line.split('\t')
                z = float(z)
                self.freq[w] = z
                # character bigram model weighted by frequency
                weight = 10 ** (z - 3)
                t = '^' + w + '$'
                for a, b in zip(t, t[1:]):
                    counts[(a, b)] = counts.get((a, b), 0) + weight
                    totals[a] = totals.get(a, 0) + weight
        self.alphabet = len({b for (_, b) in counts}) + 1
        self.bigram = {k: math.log((v + 0.01) / (totals[k[0]] + 0.01 * self.alphabet))
                       for k, v in counts.items()}
        self.totals = totals

    def zipf(self, w):
        return self.freq.get(w, 0.0)

    def avg_logprob(self, w):
        t = '^' + w + '$'
        lp = 0.0
        for a, b in zip(t, t[1:]):
            if (a, b) in self.bigram:
                lp += self.bigram[(a, b)]
            else:
                lp += math.log(0.01 / (self.totals.get(a, 0) + 0.01 * self.alphabet + 1))
        return lp / (len(t) - 1)


_EN = _FA = None


def lexicons():
    global _EN, _FA
    if _EN is None:
        d = _resource_dir()
        _EN = Lexicon(os.path.join(d, 'en.txt'))
        _FA = Lexicon(os.path.join(d, 'fa.txt'))
    return _EN, _FA


# --------------------------------------------------------------- decision ---
EN_PUNCT = '.,;:!?\'"()[]{}<>-_/\\`~'


def _clean_en(s):
    """English form for lookup; '' if the keys can't form an English word"""
    s = s.lower().rstrip('.,!?:"')
    s = s.lstrip('"(')
    return s if re.fullmatch(r"[a-z]+('[a-z]+)?", s) else ''


def _clean_fa(s):
    return normalize_fa(s.strip('.،؛:!؟?«»()[]-_/\\"\'')).replace('‌', '')


def _fa_score(fa, w):
    """frequency of Persian word, also trying it without/with zero-width joiner"""
    if not w:
        return 0.0
    best = fa.zipf(w)
    return best


def decide(en_str, fa_str, typed, context=None):
    """
    en_str : the word as it would appear in the English layout
    fa_str : the same keys as they would appear in the Persian layout
    typed  : 'en' or 'fa' - which layout was actually active
    returns (verdict, replacement, target) where verdict is
      'auto'    - confident: convert automatically
      'suggest' - probably wrong: show the bubble
      None      - leave it
    """
    EN, FA = lexicons()
    e, f = _clean_en(en_str), _clean_fa(fa_str)
    if typed == 'fa' and not e:
        return None, None, None          # keys don't make an English word
    if len(f) < 2 or (e and len(e) < 2) or any(c.isdigit() for c in en_str):
        return None, None, None
    if typed == 'en' and not any(c in PERSIAN_CHARS for c in f):
        return None, None, None          # keys don't even make Persian letters
    ez, fz = EN.zipf(e), _fa_score(FA, f)

    if typed == 'en':
        own, other, target, repl = ez, fz, 'fa', normalize_fa(fa_str)
    else:
        own, other, target, repl = fz, ez, 'en', en_str

    gap = other - own
    # the previous word was just fixed to the same language -> we are in the
    # middle of a wrongly-typed sentence, so trust the other language more
    if context == target and other >= 3.5 and gap > 0.5:
        return 'auto', repl, target
    if own >= 4.2 and gap < 2.5:         # a common word in the typed language
        return None, None, None
    if other >= 2.8 and gap >= 1.8:
        verdict = 'auto' if (gap >= 2.5 and len(f) >= 2 and other >= 3.2) else 'suggest'
        return verdict, repl, target

    # neither word is in the dictionary -> character-level guess (bubble only)
    if own == 0 and other == 0 and len(f) >= 4:
        if typed == 'en':
            lp_own = EN.avg_logprob(e) if e else -9.0
            lp_other = FA.avg_logprob(f)
        else:
            lp_own, lp_other = FA.avg_logprob(f), EN.avg_logprob(e)
        if lp_other - lp_own >= 1.6 and lp_other > -3.6:
            return 'suggest', repl, target
    return None, None, None


if __name__ == '__main__':
    for w in sys.argv[1:]:
        if any(c in PERSIAN_CHARS for c in w):
            print(w, decide(fa_to_en(w), w, 'fa'))
        else:
            print(w, decide(w, en_to_fa(w), 'en'))
