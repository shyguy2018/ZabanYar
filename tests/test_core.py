# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
import core  # noqa: E402


def fix_en_typed(w, ctx=None):
    return core.decide(w, core.en_to_fa(w), 'en', ctx)


def fix_fa_typed(w, ctx=None):
    return core.decide(core.fa_to_en(w), w, 'fa', ctx)


def test_persian_typed_on_english_layout():
    for typed, want in [('sghl', 'سلام'), ('o,fd', 'خوبی'), ('lvsd', 'مرسی'),
                        ('llk,k', 'ممنون'), ('ldo,hl', 'میخوام')]:
        verdict, repl, target = fix_en_typed(typed)
        assert verdict == 'auto' and repl == want and target == 'fa', typed


def test_english_typed_on_persian_layout():
    for typed, want in [('غخع', 'you'), ('ئثشد', 'mean'), ('اثممخ', 'hello'),
                        ('حقهزث', 'price'), ('فخئخققخص', 'tomorrow')]:
        verdict, repl, target = fix_fa_typed(typed)
        assert verdict == 'auto' and repl == want and target == 'en', typed


def test_real_words_are_left_alone():
    for w in ['hello', 'the', 'fluke', 'marmonix', 'ok', 'meter', "don't"]:
        assert fix_en_typed(w)[0] is None, w
    for w in ['سلام', 'خوبی', 'دستگاه', 'آره', 'اینو']:
        assert fix_fa_typed(w)[0] is None, w


def test_sentence_context():
    # 'شدی' is a real Persian word, but right after an English fix it means 'and'
    assert fix_fa_typed('شدی')[0] is None
    assert fix_fa_typed('شدی', ctx='en')[1] == 'and'
