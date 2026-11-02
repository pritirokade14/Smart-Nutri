from app.scoring.ingredients import find_terms, normalize


def test_normalize_ins_codes():
    n = normalize("Emulsifier (INS 322), E-471, raising agent (ins 500(ii)), stabiliser (412)")
    assert {"ins322", "ins471", "ins500", "ins412"} <= set(n.split())


def test_word_boundary_and_plural():
    assert find_terms(["roasted peanuts"], ["peanut"]) == ["peanut"]
    assert find_terms(["eggplant"], ["egg"]) == []


def test_exclude_phrases():
    assert find_terms(["cocoa butter", "sugar"], ["butter"], exclude=["cocoa butter"]) == []


def test_devanagari_terms():
    assert find_terms(["मूंगफली", "चीनी"], ["मूंगफली", "चीनी"]) == ["चीनी", "मूंगफली"]


def test_devanagari_no_match_inside_longer_word():
    assert find_terms(["दूधवाला"], ["दूध"]) == []
    assert find_terms(["दूध, चीनी"], ["दूध"]) == ["दूध"]


def test_longest_match_consumes_text():
    assert find_terms(["liquid glucose", "salt"], ["liquid glucose", "glucose"]) == ["liquid glucose"]
    assert find_terms(["onion powder"], ["onion", "onion powder"]) == ["onion powder"]
