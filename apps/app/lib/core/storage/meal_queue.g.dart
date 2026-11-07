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
  static const VerificationMeta _mealSlotIdMeta = const VerificationMeta(
    'mealSlotId',
  );
  @override
  late final GeneratedColumn<String> mealSlotId = GeneratedColumn<String>(
    'meal_slot_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _localDateMeta = const VerificationMeta(
    'localDate',
  );
  @override
  late final GeneratedColumn<String> localDate = GeneratedColumn<String>(
    'local_date',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _quickNameMeta = const VerificationMeta(
    'quickName',
  );
  @override
  late final GeneratedColumn<String> quickName = GeneratedColumn<String>(
    'quick_name',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _quickEnergyKcalMeta = const VerificationMeta(
    'quickEnergyKcal',
  );
  @override
  late final GeneratedColumn<double> quickEnergyKcal = GeneratedColumn<double>(
    'quick_energy_kcal',
    aliasedName,
    true,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _quickProteinGMeta = const VerificationMeta(
    'quickProteinG',
  );
  @override
  late final GeneratedColumn<double> quickProteinG = GeneratedColumn<double>(
    'quick_protein_g',
    aliasedName,
    true,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _quickFatGMeta = const VerificationMeta(
    'quickFatG',
  );
  @override
  late final GeneratedColumn<double> quickFatG = GeneratedColumn<double>(
    'quick_fat_g',
    aliasedName,
    true,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _quickCarbsGMeta = const VerificationMeta(
    'quickCarbsG',
  );
  @override
  late final GeneratedColumn<double> quickCarbsG = GeneratedColumn<double>(
    'quick_carbs_g',
    aliasedName,
    true,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _quickFibreGMeta = const VerificationMeta(
    'quickFibreG',
  );
  @override
  late final GeneratedColumn<double> quickFibreG = GeneratedColumn<double>(
    'quick_fibre_g',
    aliasedName,
    true,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _displayNameMeta = const VerificationMeta(
    'displayName',
  );
  @override
  late final GeneratedColumn<String> displayName = GeneratedColumn<String>(
    'display_name',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _foodIdMeta = const VerificationMeta('foodId');
  @override
  late final GeneratedColumn<String> foodId = GeneratedColumn<String>(
    'food_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _quantityMeta = const VerificationMeta(
    'quantity',
  );
  @override
  late final GeneratedColumn<double> quantity = GeneratedColumn<double>(
    'quantity',
    aliasedName,
    true,
    type: DriftSqlType.double,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _unitMeta = const VerificationMeta('unit');
  @override
  late final GeneratedColumn<String> unit = GeneratedColumn<String>(
    'unit',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
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
    mealSlotId,
    localDate,
    quickName,
    quickEnergyKcal,
    quickProteinG,
    quickFatG,
    quickCarbsG,
    quickFibreG,
    displayName,
    foodId,
    quantity,
    unit,
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
    if (data.containsKey('meal_slot_id')) {
      context.handle(
        _mealSlotIdMeta,
        mealSlotId.isAcceptableOrUnknown(
          data['meal_slot_id']!,
          _mealSlotIdMeta,
        ),
      );
    }
    if (data.containsKey('local_date')) {
      context.handle(
        _localDateMeta,
        localDate.isAcceptableOrUnknown(data['local_date']!, _localDateMeta),
      );
    }
    if (data.containsKey('quick_name')) {
      context.handle(
        _quickNameMeta,
        quickName.isAcceptableOrUnknown(data['quick_name']!, _quickNameMeta),
      );
    }
    if (data.containsKey('quick_energy_kcal')) {
      context.handle(
        _quickEnergyKcalMeta,
        quickEnergyKcal.isAcceptableOrUnknown(
          data['quick_energy_kcal']!,
          _quickEnergyKcalMeta,
        ),
      );
    }
    if (data.containsKey('quick_protein_g')) {
      context.handle(
        _quickProteinGMeta,
        quickProteinG.isAcceptableOrUnknown(
          data['quick_protein_g']!,
          _quickProteinGMeta,
        ),
      );
    }
    if (data.containsKey('quick_fat_g')) {
      context.handle(
        _quickFatGMeta,
        quickFatG.isAcceptableOrUnknown(data['quick_fat_g']!, _quickFatGMeta),
      );
    }
    if (data.containsKey('quick_carbs_g')) {
      context.handle(
        _quickCarbsGMeta,
        quickCarbsG.isAcceptableOrUnknown(
          data['quick_carbs_g']!,
          _quickCarbsGMeta,
        ),
      );
    }
    if (data.containsKey('quick_fibre_g')) {
      context.handle(
        _quickFibreGMeta,
        quickFibreG.isAcceptableOrUnknown(
          data['quick_fibre_g']!,
          _quickFibreGMeta,
        ),
      );
    }
    if (data.containsKey('display_name')) {
      context.handle(
        _displayNameMeta,
        displayName.isAcceptableOrUnknown(
          data['display_name']!,
          _displayNameMeta,
        ),
      );
    }
    if (data.containsKey('food_id')) {
      context.handle(
        _foodIdMeta,
        foodId.isAcceptableOrUnknown(data['food_id']!, _foodIdMeta),
      );
    }
    if (data.containsKey('quantity')) {
      context.handle(
        _quantityMeta,
        quantity.isAcceptableOrUnknown(data['quantity']!, _quantityMeta),
      );
    }
    if (data.containsKey('unit')) {
      context.handle(
        _unitMeta,
        unit.isAcceptableOrUnknown(data['unit']!, _unitMeta),
      );
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
      mealSlotId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}meal_slot_id'],
      ),
      localDate: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}local_date'],
      ),
      quickName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}quick_name'],
      ),
      quickEnergyKcal: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}quick_energy_kcal'],
      ),
      quickProteinG: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}quick_protein_g'],
      ),
      quickFatG: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}quick_fat_g'],
      ),
      quickCarbsG: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}quick_carbs_g'],
      ),
      quickFibreG: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}quick_fibre_g'],
      ),
      displayName: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}display_name'],
      ),
      foodId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}food_id'],
      ),
      quantity: attachedDatabase.typeMapping.read(
        DriftSqlType.double,
        data['${effectivePrefix}quantity'],
      ),
      unit: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}unit'],
      ),
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

  /// When it was eaten (stored as UTC), sent as `eaten_at` (unless
  /// [localDate] is set).
  final DateTime eatenAt;

  /// The meal slot chosen, or null (the API picks from the clock).
  final String? mealSlotId;

  /// A past day (`2026-11-06`) the entry belongs to; sent as `local_date`
  /// instead of `eaten_at`.
  final String? localDate;

  /// A quick add: set when [quickEnergyKcal] is. Blank fields stay null,
  /// never 0.
  final String? quickName;
  final double? quickEnergyKcal;
  final double? quickProteinG;
  final double? quickFatG;
  final double? quickCarbsG;
  final double? quickFibreG;

  /// The name shown on the pending row (a product name or a quick-add name).
  /// User text: never sent to analytics.
  final String? displayName;

  /// A generic food or Indian dish (`foods.id`).
  final String? foodId;

  /// A household-unit portion: [quantity] of [unit] (a unit code), instead
  /// of [grams] and [servings]. The API converts it.
  final double? quantity;
  final String? unit;
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
    this.mealSlotId,
    this.localDate,
    this.quickName,
    this.quickEnergyKcal,
    this.quickProteinG,
    this.quickFatG,
    this.quickCarbsG,
    this.quickFibreG,
    this.displayName,
    this.foodId,
    this.quantity,
    this.unit,
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
    if (!nullToAbsent || mealSlotId != null) {
      map['meal_slot_id'] = Variable<String>(mealSlotId);
    }
    if (!nullToAbsent || localDate != null) {
      map['local_date'] = Variable<String>(localDate);
    }
    if (!nullToAbsent || quickName != null) {
      map['quick_name'] = Variable<String>(quickName);
    }
    if (!nullToAbsent || quickEnergyKcal != null) {
      map['quick_energy_kcal'] = Variable<double>(quickEnergyKcal);
    }
    if (!nullToAbsent || quickProteinG != null) {
      map['quick_protein_g'] = Variable<double>(quickProteinG);
    }
    if (!nullToAbsent || quickFatG != null) {
      map['quick_fat_g'] = Variable<double>(quickFatG);
    }
    if (!nullToAbsent || quickCarbsG != null) {
      map['quick_carbs_g'] = Variable<double>(quickCarbsG);
    }
    if (!nullToAbsent || quickFibreG != null) {
      map['quick_fibre_g'] = Variable<double>(quickFibreG);
    }
    if (!nullToAbsent || displayName != null) {
      map['display_name'] = Variable<String>(displayName);
    }
    if (!nullToAbsent || foodId != null) {
      map['food_id'] = Variable<String>(foodId);
    }
    if (!nullToAbsent || quantity != null) {
      map['quantity'] = Variable<double>(quantity);
    }
    if (!nullToAbsent || unit != null) {
      map['unit'] = Variable<String>(unit);
    }
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
      mealSlotId: mealSlotId == null && nullToAbsent
          ? const Value.absent()
          : Value(mealSlotId),
      localDate: localDate == null && nullToAbsent
          ? const Value.absent()
          : Value(localDate),
      quickName: quickName == null && nullToAbsent
          ? const Value.absent()
          : Value(quickName),
      quickEnergyKcal: quickEnergyKcal == null && nullToAbsent
          ? const Value.absent()
          : Value(quickEnergyKcal),
      quickProteinG: quickProteinG == null && nullToAbsent
          ? const Value.absent()
          : Value(quickProteinG),
      quickFatG: quickFatG == null && nullToAbsent
          ? const Value.absent()
          : Value(quickFatG),
      quickCarbsG: quickCarbsG == null && nullToAbsent
          ? const Value.absent()
          : Value(quickCarbsG),
      quickFibreG: quickFibreG == null && nullToAbsent
          ? const Value.absent()
          : Value(quickFibreG),
      displayName: displayName == null && nullToAbsent
          ? const Value.absent()
          : Value(displayName),
      foodId: foodId == null && nullToAbsent
          ? const Value.absent()
          : Value(foodId),
      quantity: quantity == null && nullToAbsent
          ? const Value.absent()
          : Value(quantity),
      unit: unit == null && nullToAbsent ? const Value.absent() : Value(unit),
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
      mealSlotId: serializer.fromJson<String?>(json['mealSlotId']),
      localDate: serializer.fromJson<String?>(json['localDate']),
      quickName: serializer.fromJson<String?>(json['quickName']),
      quickEnergyKcal: serializer.fromJson<double?>(json['quickEnergyKcal']),
      quickProteinG: serializer.fromJson<double?>(json['quickProteinG']),
      quickFatG: serializer.fromJson<double?>(json['quickFatG']),
      quickCarbsG: serializer.fromJson<double?>(json['quickCarbsG']),
      quickFibreG: serializer.fromJson<double?>(json['quickFibreG']),
      displayName: serializer.fromJson<String?>(json['displayName']),
      foodId: serializer.fromJson<String?>(json['foodId']),
      quantity: serializer.fromJson<double?>(json['quantity']),
      unit: serializer.fromJson<String?>(json['unit']),
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
      'mealSlotId': serializer.toJson<String?>(mealSlotId),
      'localDate': serializer.toJson<String?>(localDate),
      'quickName': serializer.toJson<String?>(quickName),
      'quickEnergyKcal': serializer.toJson<double?>(quickEnergyKcal),
      'quickProteinG': serializer.toJson<double?>(quickProteinG),
      'quickFatG': serializer.toJson<double?>(quickFatG),
      'quickCarbsG': serializer.toJson<double?>(quickCarbsG),
      'quickFibreG': serializer.toJson<double?>(quickFibreG),
      'displayName': serializer.toJson<String?>(displayName),
      'foodId': serializer.toJson<String?>(foodId),
      'quantity': serializer.toJson<double?>(quantity),
      'unit': serializer.toJson<String?>(unit),
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
    Value<String?> mealSlotId = const Value.absent(),
    Value<String?> localDate = const Value.absent(),
    Value<String?> quickName = const Value.absent(),
    Value<double?> quickEnergyKcal = const Value.absent(),
    Value<double?> quickProteinG = const Value.absent(),
    Value<double?> quickFatG = const Value.absent(),
    Value<double?> quickCarbsG = const Value.absent(),
    Value<double?> quickFibreG = const Value.absent(),
    Value<String?> displayName = const Value.absent(),
    Value<String?> foodId = const Value.absent(),
    Value<double?> quantity = const Value.absent(),
    Value<String?> unit = const Value.absent(),
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
    mealSlotId: mealSlotId.present ? mealSlotId.value : this.mealSlotId,
    localDate: localDate.present ? localDate.value : this.localDate,
    quickName: quickName.present ? quickName.value : this.quickName,
    quickEnergyKcal: quickEnergyKcal.present
        ? quickEnergyKcal.value
        : this.quickEnergyKcal,
    quickProteinG: quickProteinG.present
        ? quickProteinG.value
        : this.quickProteinG,
    quickFatG: quickFatG.present ? quickFatG.value : this.quickFatG,
    quickCarbsG: quickCarbsG.present ? quickCarbsG.value : this.quickCarbsG,
    quickFibreG: quickFibreG.present ? quickFibreG.value : this.quickFibreG,
    displayName: displayName.present ? displayName.value : this.displayName,
    foodId: foodId.present ? foodId.value : this.foodId,
    quantity: quantity.present ? quantity.value : this.quantity,
    unit: unit.present ? unit.value : this.unit,
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
      mealSlotId: data.mealSlotId.present
          ? data.mealSlotId.value
          : this.mealSlotId,
      localDate: data.localDate.present ? data.localDate.value : this.localDate,
      quickName: data.quickName.present ? data.quickName.value : this.quickName,
      quickEnergyKcal: data.quickEnergyKcal.present
          ? data.quickEnergyKcal.value
          : this.quickEnergyKcal,
      quickProteinG: data.quickProteinG.present
          ? data.quickProteinG.value
          : this.quickProteinG,
      quickFatG: data.quickFatG.present ? data.quickFatG.value : this.quickFatG,
      quickCarbsG: data.quickCarbsG.present
          ? data.quickCarbsG.value
          : this.quickCarbsG,
      quickFibreG: data.quickFibreG.present
          ? data.quickFibreG.value
          : this.quickFibreG,
      displayName: data.displayName.present
          ? data.displayName.value
          : this.displayName,
      foodId: data.foodId.present ? data.foodId.value : this.foodId,
      quantity: data.quantity.present ? data.quantity.value : this.quantity,
      unit: data.unit.present ? data.unit.value : this.unit,
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
          ..write('mealSlotId: $mealSlotId, ')
          ..write('localDate: $localDate, ')
          ..write('quickName: $quickName, ')
          ..write('quickEnergyKcal: $quickEnergyKcal, ')
          ..write('quickProteinG: $quickProteinG, ')
          ..write('quickFatG: $quickFatG, ')
          ..write('quickCarbsG: $quickCarbsG, ')
          ..write('quickFibreG: $quickFibreG, ')
          ..write('displayName: $displayName, ')
          ..write('foodId: $foodId, ')
          ..write('quantity: $quantity, ')
          ..write('unit: $unit, ')
          ..write('attempts: $attempts, ')
          ..write('lastError: $lastError')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hashAll([
    clientId,
    memberId,
    productId,
    barcode,
    grams,
    servings,
    eatenAt,
    mealSlotId,
    localDate,
    quickName,
    quickEnergyKcal,
    quickProteinG,
    quickFatG,
    quickCarbsG,
    quickFibreG,
    displayName,
    foodId,
    quantity,
    unit,
    attempts,
    lastError,
  ]);
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
          other.mealSlotId == this.mealSlotId &&
          other.localDate == this.localDate &&
          other.quickName == this.quickName &&
          other.quickEnergyKcal == this.quickEnergyKcal &&
          other.quickProteinG == this.quickProteinG &&
          other.quickFatG == this.quickFatG &&
          other.quickCarbsG == this.quickCarbsG &&
          other.quickFibreG == this.quickFibreG &&
          other.displayName == this.displayName &&
          other.foodId == this.foodId &&
          other.quantity == this.quantity &&
          other.unit == this.unit &&
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
  final Value<String?> mealSlotId;
  final Value<String?> localDate;
  final Value<String?> quickName;
  final Value<double?> quickEnergyKcal;
  final Value<double?> quickProteinG;
  final Value<double?> quickFatG;
  final Value<double?> quickCarbsG;
  final Value<double?> quickFibreG;
  final Value<String?> displayName;
  final Value<String?> foodId;
  final Value<double?> quantity;
  final Value<String?> unit;
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
    this.mealSlotId = const Value.absent(),
    this.localDate = const Value.absent(),
    this.quickName = const Value.absent(),
    this.quickEnergyKcal = const Value.absent(),
    this.quickProteinG = const Value.absent(),
    this.quickFatG = const Value.absent(),
    this.quickCarbsG = const Value.absent(),
    this.quickFibreG = const Value.absent(),
    this.displayName = const Value.absent(),
    this.foodId = const Value.absent(),
    this.quantity = const Value.absent(),
    this.unit = const Value.absent(),
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
    this.mealSlotId = const Value.absent(),
    this.localDate = const Value.absent(),
    this.quickName = const Value.absent(),
    this.quickEnergyKcal = const Value.absent(),
    this.quickProteinG = const Value.absent(),
    this.quickFatG = const Value.absent(),
    this.quickCarbsG = const Value.absent(),
    this.quickFibreG = const Value.absent(),
    this.displayName = const Value.absent(),
    this.foodId = const Value.absent(),
    this.quantity = const Value.absent(),
    this.unit = const Value.absent(),
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
    Expression<String>? mealSlotId,
    Expression<String>? localDate,
    Expression<String>? quickName,
    Expression<double>? quickEnergyKcal,
    Expression<double>? quickProteinG,
    Expression<double>? quickFatG,
    Expression<double>? quickCarbsG,
    Expression<double>? quickFibreG,
    Expression<String>? displayName,
    Expression<String>? foodId,
    Expression<double>? quantity,
    Expression<String>? unit,
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
      if (mealSlotId != null) 'meal_slot_id': mealSlotId,
      if (localDate != null) 'local_date': localDate,
      if (quickName != null) 'quick_name': quickName,
      if (quickEnergyKcal != null) 'quick_energy_kcal': quickEnergyKcal,
      if (quickProteinG != null) 'quick_protein_g': quickProteinG,
      if (quickFatG != null) 'quick_fat_g': quickFatG,
      if (quickCarbsG != null) 'quick_carbs_g': quickCarbsG,
      if (quickFibreG != null) 'quick_fibre_g': quickFibreG,
      if (displayName != null) 'display_name': displayName,
      if (foodId != null) 'food_id': foodId,
      if (quantity != null) 'quantity': quantity,
      if (unit != null) 'unit': unit,
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
    Value<String?>? mealSlotId,
    Value<String?>? localDate,
    Value<String?>? quickName,
    Value<double?>? quickEnergyKcal,
    Value<double?>? quickProteinG,
    Value<double?>? quickFatG,
    Value<double?>? quickCarbsG,
    Value<double?>? quickFibreG,
    Value<String?>? displayName,
    Value<String?>? foodId,
    Value<double?>? quantity,
    Value<String?>? unit,
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
      mealSlotId: mealSlotId ?? this.mealSlotId,
      localDate: localDate ?? this.localDate,
      quickName: quickName ?? this.quickName,
      quickEnergyKcal: quickEnergyKcal ?? this.quickEnergyKcal,
      quickProteinG: quickProteinG ?? this.quickProteinG,
      quickFatG: quickFatG ?? this.quickFatG,
      quickCarbsG: quickCarbsG ?? this.quickCarbsG,
      quickFibreG: quickFibreG ?? this.quickFibreG,
      displayName: displayName ?? this.displayName,
      foodId: foodId ?? this.foodId,
      quantity: quantity ?? this.quantity,
      unit: unit ?? this.unit,
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
    if (mealSlotId.present) {
      map['meal_slot_id'] = Variable<String>(mealSlotId.value);
    }
    if (localDate.present) {
      map['local_date'] = Variable<String>(localDate.value);
    }
    if (quickName.present) {
      map['quick_name'] = Variable<String>(quickName.value);
    }
    if (quickEnergyKcal.present) {
      map['quick_energy_kcal'] = Variable<double>(quickEnergyKcal.value);
    }
    if (quickProteinG.present) {
      map['quick_protein_g'] = Variable<double>(quickProteinG.value);
    }
    if (quickFatG.present) {
      map['quick_fat_g'] = Variable<double>(quickFatG.value);
    }
    if (quickCarbsG.present) {
      map['quick_carbs_g'] = Variable<double>(quickCarbsG.value);
    }
    if (quickFibreG.present) {
      map['quick_fibre_g'] = Variable<double>(quickFibreG.value);
    }
    if (displayName.present) {
      map['display_name'] = Variable<String>(displayName.value);
    }
    if (foodId.present) {
      map['food_id'] = Variable<String>(foodId.value);
    }
    if (quantity.present) {
      map['quantity'] = Variable<double>(quantity.value);
    }
    if (unit.present) {
      map['unit'] = Variable<String>(unit.value);
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
          ..write('mealSlotId: $mealSlotId, ')
          ..write('localDate: $localDate, ')
          ..write('quickName: $quickName, ')
          ..write('quickEnergyKcal: $quickEnergyKcal, ')
          ..write('quickProteinG: $quickProteinG, ')
          ..write('quickFatG: $quickFatG, ')
          ..write('quickCarbsG: $quickCarbsG, ')
          ..write('quickFibreG: $quickFibreG, ')
          ..write('displayName: $displayName, ')
          ..write('foodId: $foodId, ')
          ..write('quantity: $quantity, ')
          ..write('unit: $unit, ')
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
      Value<String?> mealSlotId,
      Value<String?> localDate,
      Value<String?> quickName,
      Value<double?> quickEnergyKcal,
      Value<double?> quickProteinG,
      Value<double?> quickFatG,
      Value<double?> quickCarbsG,
      Value<double?> quickFibreG,
      Value<String?> displayName,
      Value<String?> foodId,
      Value<double?> quantity,
      Value<String?> unit,
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
      Value<String?> mealSlotId,
      Value<String?> localDate,
      Value<String?> quickName,
      Value<double?> quickEnergyKcal,
      Value<double?> quickProteinG,
      Value<double?> quickFatG,
      Value<double?> quickCarbsG,
      Value<double?> quickFibreG,
      Value<String?> displayName,
      Value<String?> foodId,
      Value<double?> quantity,
      Value<String?> unit,
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

  ColumnFilters<String> get mealSlotId => $composableBuilder(
    column: $table.mealSlotId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get localDate => $composableBuilder(
    column: $table.localDate,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get quickName => $composableBuilder(
    column: $table.quickName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get quickEnergyKcal => $composableBuilder(
    column: $table.quickEnergyKcal,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get quickProteinG => $composableBuilder(
    column: $table.quickProteinG,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get quickFatG => $composableBuilder(
    column: $table.quickFatG,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get quickCarbsG => $composableBuilder(
    column: $table.quickCarbsG,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get quickFibreG => $composableBuilder(
    column: $table.quickFibreG,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get displayName => $composableBuilder(
    column: $table.displayName,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get foodId => $composableBuilder(
    column: $table.foodId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<double> get quantity => $composableBuilder(
    column: $table.quantity,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get unit => $composableBuilder(
    column: $table.unit,
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

  ColumnOrderings<String> get mealSlotId => $composableBuilder(
    column: $table.mealSlotId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get localDate => $composableBuilder(
    column: $table.localDate,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get quickName => $composableBuilder(
    column: $table.quickName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get quickEnergyKcal => $composableBuilder(
    column: $table.quickEnergyKcal,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get quickProteinG => $composableBuilder(
    column: $table.quickProteinG,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get quickFatG => $composableBuilder(
    column: $table.quickFatG,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get quickCarbsG => $composableBuilder(
    column: $table.quickCarbsG,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get quickFibreG => $composableBuilder(
    column: $table.quickFibreG,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get displayName => $composableBuilder(
    column: $table.displayName,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get foodId => $composableBuilder(
    column: $table.foodId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<double> get quantity => $composableBuilder(
    column: $table.quantity,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get unit => $composableBuilder(
    column: $table.unit,
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

  GeneratedColumn<String> get mealSlotId => $composableBuilder(
    column: $table.mealSlotId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get localDate =>
      $composableBuilder(column: $table.localDate, builder: (column) => column);

  GeneratedColumn<String> get quickName =>
      $composableBuilder(column: $table.quickName, builder: (column) => column);

  GeneratedColumn<double> get quickEnergyKcal => $composableBuilder(
    column: $table.quickEnergyKcal,
    builder: (column) => column,
  );

  GeneratedColumn<double> get quickProteinG => $composableBuilder(
    column: $table.quickProteinG,
    builder: (column) => column,
  );

  GeneratedColumn<double> get quickFatG =>
      $composableBuilder(column: $table.quickFatG, builder: (column) => column);

  GeneratedColumn<double> get quickCarbsG => $composableBuilder(
    column: $table.quickCarbsG,
    builder: (column) => column,
  );

  GeneratedColumn<double> get quickFibreG => $composableBuilder(
    column: $table.quickFibreG,
    builder: (column) => column,
  );

  GeneratedColumn<String> get displayName => $composableBuilder(
    column: $table.displayName,
    builder: (column) => column,
  );

  GeneratedColumn<String> get foodId =>
      $composableBuilder(column: $table.foodId, builder: (column) => column);

  GeneratedColumn<double> get quantity =>
      $composableBuilder(column: $table.quantity, builder: (column) => column);

  GeneratedColumn<String> get unit =>
      $composableBuilder(column: $table.unit, builder: (column) => column);

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
                Value<String?> mealSlotId = const Value.absent(),
                Value<String?> localDate = const Value.absent(),
                Value<String?> quickName = const Value.absent(),
                Value<double?> quickEnergyKcal = const Value.absent(),
                Value<double?> quickProteinG = const Value.absent(),
                Value<double?> quickFatG = const Value.absent(),
                Value<double?> quickCarbsG = const Value.absent(),
                Value<double?> quickFibreG = const Value.absent(),
                Value<String?> displayName = const Value.absent(),
                Value<String?> foodId = const Value.absent(),
                Value<double?> quantity = const Value.absent(),
                Value<String?> unit = const Value.absent(),
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
                mealSlotId: mealSlotId,
                localDate: localDate,
                quickName: quickName,
                quickEnergyKcal: quickEnergyKcal,
                quickProteinG: quickProteinG,
                quickFatG: quickFatG,
                quickCarbsG: quickCarbsG,
                quickFibreG: quickFibreG,
                displayName: displayName,
                foodId: foodId,
                quantity: quantity,
                unit: unit,
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
                Value<String?> mealSlotId = const Value.absent(),
                Value<String?> localDate = const Value.absent(),
                Value<String?> quickName = const Value.absent(),
                Value<double?> quickEnergyKcal = const Value.absent(),
                Value<double?> quickProteinG = const Value.absent(),
                Value<double?> quickFatG = const Value.absent(),
                Value<double?> quickCarbsG = const Value.absent(),
                Value<double?> quickFibreG = const Value.absent(),
                Value<String?> displayName = const Value.absent(),
                Value<String?> foodId = const Value.absent(),
                Value<double?> quantity = const Value.absent(),
                Value<String?> unit = const Value.absent(),
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
                mealSlotId: mealSlotId,
                localDate: localDate,
                quickName: quickName,
                quickEnergyKcal: quickEnergyKcal,
                quickProteinG: quickProteinG,
                quickFatG: quickFatG,
                quickCarbsG: quickCarbsG,
                quickFibreG: quickFibreG,
                displayName: displayName,
                foodId: foodId,
                quantity: quantity,
                unit: unit,
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
