// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'meal_queue.dart';

// ignore_for_file: type=lint
class $PendingMealsTable extends PendingMeals
    with TableInfo<$PendingMealsTable, PendingMeal> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $PendingMealsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _clientIdMeta = const VerificationMeta(
    'clientId',
  );
  @override
  late final GeneratedColumn<String> clientId = GeneratedColumn<String>(
    'client_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _memberIdMeta = const VerificationMeta(
    'memberId',
  );
  @override
  late final GeneratedColumn<String> memberId = GeneratedColumn<String>(
    'member_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _productIdMeta = const VerificationMeta(
    'productId',
  );
  @override
  late final GeneratedColumn<String> productId = GeneratedColumn<String>(
    'product_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _barcodeMeta = const VerificationMeta(
    'barcode',
  );
  @override
  late final GeneratedColumn<String> barcode = GeneratedColumn<String>(
    'barcode',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _gramsMeta = const VerificationMeta('grams');
  @override
  late final GeneratedColumn<double> grams = GeneratedColumn<double>(
    'grams',
    aliasedName,
    true,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _servingsMeta = const VerificationMeta(
    'servings',
  );
  @override
  late final GeneratedColumn<double> servings = GeneratedColumn<double>(
    'servings',
    aliasedName,
    true,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _eatenAtMeta = const VerificationMeta(
    'eatenAt',
  );
  @override
  late final GeneratedColumn<DateTime> eatenAt = GeneratedColumn<DateTime>(
    'eaten_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _attemptsMeta = const VerificationMeta(
    'attempts',
  );
  @override
  late final GeneratedColumn<int> attempts = GeneratedColumn<int>(
    'attempts',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
    defaultValue: const Constant(0),
  );
  static const VerificationMeta _lastErrorMeta = const VerificationMeta(
    'lastError',
  );
  @override
  late final GeneratedColumn<String> lastError = GeneratedColumn<String>(
    'last_error',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  @override
  List<GeneratedColumn> get $columns => [
    clientId,
    memberId,
    productId,
    barcode,
    grams,
    servings,
    eatenAt,
    attempts,
    lastError,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'pending_meals';
  @override
  VerificationContext validateIntegrity(
    Insertable<PendingMeal> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('client_id')) {
      context.handle(
        _clientIdMeta,
        clientId.isAcceptableOrUnknown(data['client_id']!, _clientIdMeta),
      );
    } else if (isInserting) {
      context.missing(_clientIdMeta);
    }
    if (data.containsKey('member_id')) {
      context.handle(
        _memberIdMeta,
        memberId.isAcceptableOrUnknown(data['member_id']!, _memberIdMeta),
      );
    } else if (isInserting) {
      context.missing(_memberIdMeta);
    }
    if (data.containsKey('product_id')) {
      context.handle(
        _productIdMeta,
        productId.isAcceptableOrUnknown(data['product_id']!, _productIdMeta),
      );
    }
    if (data.containsKey('barcode')) {
      context.handle(
        _barcodeMeta,
        barcode.isAcceptableOrUnknown(data['barcode']!, _barcodeMeta),
      );
    }
    if (data.containsKey('grams')) {
      context.handle(
        _gramsMeta,
        grams.isAcceptableOrUnknown(data['grams']!, _gramsMeta),
      );
    }
    if (data.containsKey('servings')) {
      context.handle(
        _servingsMeta,
        servings.isAcceptableOrUnknown(data['servings']!, _servingsMeta),
      );
    }
    if (data.containsKey('eaten_at')) {
      context.handle(
        _eatenAtMeta,
        eatenAt.isAcceptableOrUnknown(data['eaten_at']!, _eatenAtMeta),
      );
    } else if (isInserting) {
      context.missing(_eatenAtMeta);
    }
    if (data.containsKey('attempts')) {
      context.handle(
        _attemptsMeta,
        attempts.isAcceptableOrUnknown(data['attempts']!, _attemptsMeta),
      );
    }
    if (data.containsKey('last_error')) {
      context.handle(
        _lastErrorMeta,
        lastError.isAcceptableOrUnknown(data['last_error']!, _lastErrorMeta),
      );
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {clientId};
  @override
  PendingMeal map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return PendingMeal(
      clientId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}client_id'],
      )!,
      memberId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}member_id'],
      )!,
      productId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}product_id'],
      ),
      barcode: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}barcode'],
      ),
      grams: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}grams'],
      ),
      servings: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}servings'],
      ),
      eatenAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}eaten_at'],
      )!,
      attempts: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}attempts'],
      )!,
      lastError: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}last_error'],
      ),
    );
  }

  @override
  $PendingMealsTable createAlias(String alias) {
    return $PendingMealsTable(attachedDatabase, alias);
  }
}

class PendingMeal extends DataClass implements Insertable<PendingMeal> {
  final String clientId;
  final String memberId;

  /// Exactly one of [productId] (our product) and [barcode] (an Open Food
  /// Facts product) is set.
  final String? productId;
  final String? barcode;

  /// Exactly one of [grams] and [servings] is set.
  final double? grams;
  final double? servings;

  /// When it was eaten (stored as UTC), sent as `eaten_at`.
  final DateTime eatenAt;
  final int attempts;
  final String? lastError;
  const PendingMeal({
    required this.clientId,
    required this.memberId,
    this.productId,
    this.barcode,
    this.grams,
    this.servings,
    required this.eatenAt,
    required this.attempts,
    this.lastError,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['client_id'] = Variable<String>(clientId);
    map['member_id'] = Variable<String>(memberId);
    if (!nullToAbsent || productId != null) {
      map['product_id'] = Variable<String>(productId);
    }
    if (!nullToAbsent || barcode != null) {
      map['barcode'] = Variable<String>(barcode);
    }
    if (!nullToAbsent || grams != null) {
      map['grams'] = Variable<double>(grams);
    }
    if (!nullToAbsent || servings != null) {
      map['servings'] = Variable<double>(servings);
    }
    map['eaten_at'] = Variable<DateTime>(eatenAt);
    map['attempts'] = Variable<int>(attempts);
    if (!nullToAbsent || lastError != null) {
      map['last_error'] = Variable<String>(lastError);
    }
    return map;
  }

  PendingMealsCompanion toCompanion(bool nullToAbsent) {
    return PendingMealsCompanion(
      clientId: Value(clientId),
      memberId: Value(memberId),
      productId: productId == null && nullToAbsent
          ? const Value.absent()
          : Value(productId),
      barcode: barcode == null && nullToAbsent
          ? const Value.absent()
          : Value(barcode),
      grams: grams == null && nullToAbsent
          ? const Value.absent()
          : Value(grams),
      servings: servings == null && nullToAbsent
          ? const Value.absent()
          : Value(servings),
      eatenAt: Value(eatenAt),
      attempts: Value(attempts),
      lastError: lastError == null && nullToAbsent
          ? const Value.absent()
          : Value(lastError),
    );
  }

  factory PendingMeal.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return PendingMeal(
      clientId: serializer.fromJson<String>(json['clientId']),
      memberId: serializer.fromJson<String>(json['memberId']),
      productId: serializer.fromJson<String?>(json['productId']),
      barcode: serializer.fromJson<String?>(json['barcode']),
      grams: serializer.fromJson<double?>(json['grams']),
      servings: serializer.fromJson<double?>(json['servings']),
      eatenAt: serializer.fromJson<DateTime>(json['eatenAt']),
      attempts: serializer.fromJson<int>(json['attempts']),
      lastError: serializer.fromJson<String?>(json['lastError']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'clientId': serializer.toJson<String>(clientId),
      'memberId': serializer.toJson<String>(memberId),
      'productId': serializer.toJson<String?>(productId),
      'barcode': serializer.toJson<String?>(barcode),
      'grams': serializer.toJson<double?>(grams),
      'servings': serializer.toJson<double?>(servings),
      'eatenAt': serializer.toJson<DateTime>(eatenAt),
      'attempts': serializer.toJson<int>(attempts),
      'lastError': serializer.toJson<String?>(lastError),
    };
  }

  PendingMeal copyWith({
    String? clientId,
    String? memberId,
    Value<String?> productId = const Value.absent(),
    Value<String?> barcode = const Value.absent(),
    Value<double?> grams = const Value.absent(),
    Value<double?> servings = const Value.absent(),
    DateTime? eatenAt,
    int? attempts,
    Value<String?> lastError = const Value.absent(),
  }) => PendingMeal(
    clientId: clientId ?? this.clientId,
    memberId: memberId ?? this.memberId,
    productId: productId.present ? productId.value : this.productId,
    barcode: barcode.present ? barcode.value : this.barcode,
    grams: grams.present ? grams.value : this.grams,
    servings: servings.present ? servings.value : this.servings,
    eatenAt: eatenAt ?? this.eatenAt,
    attempts: attempts ?? this.attempts,
    lastError: lastError.present ? lastError.value : this.lastError,
  );
  PendingMeal copyWithCompanion(PendingMealsCompanion data) {
    return PendingMeal(
      clientId: data.clientId.present ? data.clientId.value : this.clientId,
      memberId: data.memberId.present ? data.memberId.value : this.memberId,
      productId: data.productId.present ? data.productId.value : this.productId,
      barcode: data.barcode.present ? data.barcode.value : this.barcode,
      grams: data.grams.present ? data.grams.value : this.grams,
      servings: data.servings.present ? data.servings.value : this.servings,
      eatenAt: data.eatenAt.present ? data.eatenAt.value : this.eatenAt,
      attempts: data.attempts.present ? data.attempts.value : this.attempts,
      lastError: data.lastError.present ? data.lastError.value : this.lastError,
    );
  }

  @override
  String toString() {
    return (StringBuffer('PendingMeal(')
          ..write('clientId: $clientId, ')
          ..write('memberId: $memberId, ')
          ..write('productId: $productId, ')
          ..write('barcode: $barcode, ')
          ..write('grams: $grams, ')
          ..write('servings: $servings, ')
          ..write('eatenAt: $eatenAt, ')
          ..write('attempts: $attempts, ')
          ..write('lastError: $lastError')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    clientId,
    memberId,
    productId,
    barcode,
    grams,
    servings,
    eatenAt,
    attempts,
    lastError,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is PendingMeal &&
          other.clientId == this.clientId &&
          other.memberId == this.memberId &&
          other.productId == this.productId &&
          other.barcode == this.barcode &&
          other.grams == this.grams &&
          other.servings == this.servings &&
          other.eatenAt == this.eatenAt &&
          other.attempts == this.attempts &&
          other.lastError == this.lastError);
}

class PendingMealsCompanion extends UpdateCompanion<PendingMeal> {
  final Value<String> clientId;
  final Value<String> memberId;
  final Value<String?> productId;
  final Value<String?> barcode;
  final Value<double?> grams;
  final Value<double?> servings;
  final Value<DateTime> eatenAt;
  final Value<int> attempts;
  final Value<String?> lastError;
  final Value<int> rowid;
  const PendingMealsCompanion({
    this.clientId = const Value.absent(),
    this.memberId = const Value.absent(),
    this.productId = const Value.absent(),
    this.barcode = const Value.absent(),
    this.grams = const Value.absent(),
    this.servings = const Value.absent(),
    this.eatenAt = const Value.absent(),
    this.attempts = const Value.absent(),
    this.lastError = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  PendingMealsCompanion.insert({
    required String clientId,
    required String memberId,
    this.productId = const Value.absent(),
    this.barcode = const Value.absent(),
    this.grams = const Value.absent(),
    this.servings = const Value.absent(),
    required DateTime eatenAt,
    this.attempts = const Value.absent(),
    this.lastError = const Value.absent(),
    this.rowid = const Value.absent(),
  }) : clientId = Value(clientId),
       memberId = Value(memberId),
       eatenAt = Value(eatenAt);
  static Insertable<PendingMeal> custom({
    Expression<String>? clientId,
    Expression<String>? memberId,
    Expression<String>? productId,
    Expression<String>? barcode,
    Expression<double>? grams,
    Expression<double>? servings,
    Expression<DateTime>? eatenAt,
    Expression<int>? attempts,
    Expression<String>? lastError,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (clientId != null) 'client_id': clientId,
      if (memberId != null) 'member_id': memberId,
      if (productId != null) 'product_id': productId,
      if (barcode != null) 'barcode': barcode,
      if (grams != null) 'grams': grams,
      if (servings != null) 'servings': servings,
      if (eatenAt != null) 'eaten_at': eatenAt,
      if (attempts != null) 'attempts': attempts,
      if (lastError != null) 'last_error': lastError,
      if (rowid != null) 'rowid': rowid,
    });
  }

  PendingMealsCompanion copyWith({
    Value<String>? clientId,
    Value<String>? memberId,
    Value<String?>? productId,
    Value<String?>? barcode,
    Value<double?>? grams,
    Value<double?>? servings,
    Value<DateTime>? eatenAt,
    Value<int>? attempts,
    Value<String?>? lastError,
    Value<int>? rowid,
  }) {
    return PendingMealsCompanion(
      clientId: clientId ?? this.clientId,
      memberId: memberId ?? this.memberId,
      productId: productId ?? this.productId,
      barcode: barcode ?? this.barcode,
      grams: grams ?? this.grams,
      servings: servings ?? this.servings,
      eatenAt: eatenAt ?? this.eatenAt,
      attempts: attempts ?? this.attempts,
      lastError: lastError ?? this.lastError,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (clientId.present) {
      map['client_id'] = Variable<String>(clientId.value);
    }
    if (memberId.present) {
      map['member_id'] = Variable<String>(memberId.value);
    }
    if (productId.present) {
      map['product_id'] = Variable<String>(productId.value);
    }
    if (barcode.present) {
      map['barcode'] = Variable<String>(barcode.value);
    }
    if (grams.present) {
      map['grams'] = Variable<double>(grams.value);
    }
    if (servings.present) {
      map['servings'] = Variable<double>(servings.value);
    }
    if (eatenAt.present) {
      map['eaten_at'] = Variable<DateTime>(eatenAt.value);
    }
    if (attempts.present) {
      map['attempts'] = Variable<int>(attempts.value);
    }
    if (lastError.present) {
      map['last_error'] = Variable<String>(lastError.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('PendingMealsCompanion(')
          ..write('clientId: $clientId, ')
          ..write('memberId: $memberId, ')
          ..write('productId: $productId, ')
          ..write('barcode: $barcode, ')
          ..write('grams: $grams, ')
          ..write('servings: $servings, ')
          ..write('eatenAt: $eatenAt, ')
          ..write('attempts: $attempts, ')
          ..write('lastError: $lastError, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$MealQueueDatabase extends GeneratedDatabase {
  _$MealQueueDatabase(QueryExecutor e) : super(e);
  $MealQueueDatabaseManager get managers => $MealQueueDatabaseManager(this);
  late final $PendingMealsTable pendingMeals = $PendingMealsTable(this);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [pendingMeals];
}

typedef $$PendingMealsTableCreateCompanionBuilder =
    PendingMealsCompanion Function({
      required String clientId,
      required String memberId,
      Value<String?> productId,
      Value<String?> barcode,
      Value<double?> grams,
      Value<double?> servings,
      required DateTime eatenAt,
      Value<int> attempts,
      Value<String?> lastError,
      Value<int> rowid,
    });
typedef $$PendingMealsTableUpdateCompanionBuilder =
    PendingMealsCompanion Function({
      Value<String> clientId,
      Value<String> memberId,
      Value<String?> productId,
      Value<String?> barcode,
      Value<double?> grams,
      Value<double?> servings,
      Value<DateTime> eatenAt,
      Value<int> attempts,
      Value<String?> lastError,
      Value<int> rowid,
    });

class $$PendingMealsTableFilterComposer
    extends Composer<_$MealQueueDatabase, $PendingMealsTable> {
  $$PendingMealsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get clientId => $composableBuilder(
    column: $table.clientId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get memberId => $composableBuilder(
    column: $table.memberId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get productId => $composableBuilder(
    column: $table.productId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get barcode => $composableBuilder(
    column: $table.barcode,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get grams => $composableBuilder(
    column: $table.grams,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get servings => $composableBuilder(
    column: $table.servings,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get eatenAt => $composableBuilder(
    column: $table.eatenAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get attempts => $composableBuilder(
    column: $table.attempts,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnFilters(column),
  );
}

class $$PendingMealsTableOrderingComposer
    extends Composer<_$MealQueueDatabase, $PendingMealsTable> {
  $$PendingMealsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get clientId => $composableBuilder(
    column: $table.clientId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get memberId => $composableBuilder(
    column: $table.memberId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get productId => $composableBuilder(
    column: $table.productId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get barcode => $composableBuilder(
    column: $table.barcode,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get grams => $composableBuilder(
    column: $table.grams,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get servings => $composableBuilder(
    column: $table.servings,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get eatenAt => $composableBuilder(
    column: $table.eatenAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get attempts => $composableBuilder(
    column: $table.attempts,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get lastError => $composableBuilder(
    column: $table.lastError,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$PendingMealsTableAnnotationComposer
    extends Composer<_$MealQueueDatabase, $PendingMealsTable> {
  $$PendingMealsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get clientId =>
      $composableBuilder(column: $table.clientId, builder: (column) => column);

  GeneratedColumn<String> get memberId =>
      $composableBuilder(column: $table.memberId, builder: (column) => column);

  GeneratedColumn<String> get productId =>
      $composableBuilder(column: $table.productId, builder: (column) => column);

  GeneratedColumn<String> get barcode =>
      $composableBuilder(column: $table.barcode, builder: (column) => column);

  GeneratedColumn<double> get grams =>
      $composableBuilder(column: $table.grams, builder: (column) => column);

  GeneratedColumn<double> get servings =>
      $composableBuilder(column: $table.servings, builder: (column) => column);

  GeneratedColumn<DateTime> get eatenAt =>
      $composableBuilder(column: $table.eatenAt, builder: (column) => column);

  GeneratedColumn<int> get attempts =>
      $composableBuilder(column: $table.attempts, builder: (column) => column);

  GeneratedColumn<String> get lastError =>
      $composableBuilder(column: $table.lastError, builder: (column) => column);
}

class $$PendingMealsTableTableManager
    extends
        RootTableManager<
          _$MealQueueDatabase,
          $PendingMealsTable,
          PendingMeal,
          $$PendingMealsTableFilterComposer,
          $$PendingMealsTableOrderingComposer,
          $$PendingMealsTableAnnotationComposer,
          $$PendingMealsTableCreateCompanionBuilder,
          $$PendingMealsTableUpdateCompanionBuilder,
          (
            PendingMeal,
            BaseReferences<
              _$MealQueueDatabase,
              $PendingMealsTable,
              PendingMeal
            >,
          ),
          PendingMeal,
          PrefetchHooks Function()
        > {
  $$PendingMealsTableTableManager(
    _$MealQueueDatabase db,
    $PendingMealsTable table,
  ) : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$PendingMealsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$PendingMealsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$PendingMealsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> clientId = const Value.absent(),
                Value<String> memberId = const Value.absent(),
                Value<String?> productId = const Value.absent(),
                Value<String?> barcode = const Value.absent(),
                Value<double?> grams = const Value.absent(),
                Value<double?> servings = const Value.absent(),
                Value<DateTime> eatenAt = const Value.absent(),
                Value<int> attempts = const Value.absent(),
                Value<String?> lastError = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => PendingMealsCompanion(
                clientId: clientId,
                memberId: memberId,
                productId: productId,
                barcode: barcode,
                grams: grams,
                servings: servings,
                eatenAt: eatenAt,
                attempts: attempts,
                lastError: lastError,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String clientId,
                required String memberId,
                Value<String?> productId = const Value.absent(),
                Value<String?> barcode = const Value.absent(),
                Value<double?> grams = const Value.absent(),
                Value<double?> servings = const Value.absent(),
                required DateTime eatenAt,
                Value<int> attempts = const Value.absent(),
                Value<String?> lastError = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => PendingMealsCompanion.insert(
                clientId: clientId,
                memberId: memberId,
                productId: productId,
                barcode: barcode,
                grams: grams,
                servings: servings,
                eatenAt: eatenAt,
                attempts: attempts,
                lastError: lastError,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$PendingMealsTableProcessedTableManager =
    ProcessedTableManager<
      _$MealQueueDatabase,
      $PendingMealsTable,
      PendingMeal,
      $$PendingMealsTableFilterComposer,
      $$PendingMealsTableOrderingComposer,
      $$PendingMealsTableAnnotationComposer,
      $$PendingMealsTableCreateCompanionBuilder,
      $$PendingMealsTableUpdateCompanionBuilder,
      (
        PendingMeal,
        BaseReferences<_$MealQueueDatabase, $PendingMealsTable, PendingMeal>,
      ),
      PendingMeal,
      PrefetchHooks Function()
    >;

class $MealQueueDatabaseManager {
  final _$MealQueueDatabase _db;
  $MealQueueDatabaseManager(this._db);
  $$PendingMealsTableTableManager get pendingMeals =>
      $$PendingMealsTableTableManager(_db, _db.pendingMeals);
}
