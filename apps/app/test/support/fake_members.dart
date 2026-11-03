import 'package:smartnutri_api/src/export.dart';

/// Builds a [MemberOut] the way the API returns it.
MemberOut memberOut({
  String id = 'm1',
  String name = 'Asha',
  MemberOutRelation relation = MemberOutRelation.child,
  int? birthYear = 2015,
  MemberOutSex? sex,
  num? heightCm,
  num? weightKg,
  MemberOutDiet diet = MemberOutDiet.veg,
  List<String> allergens = const [],
  List<MemberOutConditions> conditions = const [],
  List<MemberOutCustomAlerts> customAlerts = const [],
  MemberOutGoal? goal,
  bool isPrimary = false,
}) => MemberOut(
  id: id,
  name: name,
  relation: relation,
  birthYear: birthYear,
  sex: sex,
  heightCm: heightCm,
  weightKg: weightKg,
  diet: diet,
  allergens: allergens,
  conditions: conditions,
  customAlerts: customAlerts,
  goal: goal,
  isPrimary: isPrimary,
);

MemberOut primaryMember({String name = 'Ravi'}) => memberOut(
  id: 'p1',
  name: name,
  relation: MemberOutRelation.self,
  birthYear: 1985,
  diet: MemberOutDiet.nonVeg,
  isPrimary: true,
);

/// Records every call; [error] (when set) is thrown by the next write.
class FakeMembersClient implements MembersClient {
  FakeMembersClient([List<MemberOut>? members])
    : members = members ?? [primaryMember()];

  final List<MemberOut> members;
  final calls = <String>[];
  final created = <MemberIn>[];
  final patched = <(String, MemberPatch)>[];
  final deleted = <String>[];

  /// Thrown by the next create/update/delete, then cleared.
  Object? error;

  void _maybeThrow() {
    final e = error;
    if (e != null) {
      error = null;
      throw e;
    }
  }

  @override
  Future<List<MemberOut>> membersList() async {
    calls.add('list');
    return [...members];
  }

  @override
  Future<MemberOut> membersCreate({required MemberIn body}) async {
    calls.add('create');
    created.add(body);
    _maybeThrow();
    final json = body.toJson();
    final m = MemberOut.fromJson({
      ...json,
      'id': 'new${created.length}',
      'is_primary': false,
      'goal': json['goal'],
      'sex': json['sex'],
      'height_cm': json['height_cm'],
      'weight_kg': json['weight_kg'],
    });
    members.add(m);
    return m;
  }

  @override
  Future<MemberOut> membersUpdate({
    required String memberId,
    required MemberPatch body,
  }) async {
    calls.add('update');
    patched.add((memberId, body));
    _maybeThrow();
    final i = members.indexWhere((m) => m.id == memberId);
    final old = members[i].toJson();
    final patch = body.toJson()..removeWhere((k, v) => v == null);
    final m = MemberOut.fromJson({...old, ...patch});
    members[i] = m;
    return m;
  }

  @override
  Future<void> membersDelete({required String memberId}) async {
    calls.add('delete');
    deleted.add(memberId);
    _maybeThrow();
    members.removeWhere((m) => m.id == memberId);
  }

  @override
  Future<MemberOut> membersGet({required String memberId}) async =>
      members.firstWhere((m) => m.id == memberId);
}

const consentVersions = {
  'terms': '2026-11-01',
  'health_data': '2026-11-02',
  'ai_processing': '2026-11-03',
};

/// Consent states keyed by purpose; records every `consentsRecord` body.
class FakeConsentsClient implements ConsentsClient {
  FakeConsentsClient({
    Set<String> granted = const {},
    this.withdrawn = const {},
    Set<String> needsUpdate = const {},
  }) : granted = {...granted},
       needsUpdate = {...needsUpdate};

  final Set<String> granted;

  /// Purposes agreed once and since withdrawn (version set, not granted).
  final Set<String> withdrawn;

  /// Purposes agreed at an older version: not granted, `needs_update`.
  final Set<String> needsUpdate;
  final recorded = <ConsentIn>[];
  int listCalls = 0;

  /// Thrown by the next list calls, in order.
  final listErrors = <Object>[];

  List<ConsentState> _states() => [
    for (final MapEntry(key: purpose, value: version)
        in consentVersions.entries)
      ConsentState(
        purpose: purpose,
        granted: granted.contains(purpose),
        version: needsUpdate.contains(purpose)
            ? '2025-01-01'
            : granted.contains(purpose) || withdrawn.contains(purpose)
            ? version
            : null,
        currentVersion: version,
        needsUpdate: needsUpdate.contains(purpose),
      ),
  ];

  @override
  Future<List<ConsentState>> consentsList() async {
    listCalls++;
    if (listErrors.isNotEmpty) throw listErrors.removeAt(0);
    return _states();
  }

  @override
  Future<List<ConsentState>> consentsRecord({required ConsentIn body}) async {
    recorded.add(body);
    final purpose = body.purpose.json!;
    body.granted ? granted.add(purpose) : granted.remove(purpose);
    needsUpdate.remove(purpose);
    return _states();
  }
}
