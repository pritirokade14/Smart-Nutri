/// `member_N` tokens in the AI explanation (`ExplanationOut.text` and
/// `tips`). The model never sees names; the API maps each token to a member
/// id in `member_refs`.
final _memberToken = RegExp(r'member_\d+');

/// Replaces every `member_N` token in [text] with that member's name.
///
/// The longest token always wins (`member_10` is one token, never `member_1`
/// followed by "0"), because the pattern takes all the digits. Returns null
/// when any token has no member (missing from [memberRefs], or its id is not
/// in [namesById]): the caller then hides the explanation rather than show a
/// raw token or the wrong person.
String? substituteMemberTokens(
  String text,
  Map<String, String> memberRefs,
  Map<String, String> namesById,
) {
  var unresolved = false;
  final out = text.replaceAllMapped(_memberToken, (m) {
    final name = namesById[memberRefs[m[0]]];
    if (name == null) {
      unresolved = true;
      return m[0]!;
    }
    return name;
  });
  return unresolved ? null : out;
}
