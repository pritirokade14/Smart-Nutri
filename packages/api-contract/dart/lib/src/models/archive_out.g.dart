// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'archive_out.dart';

// **************************************************************************
// JsonSerializableGenerator
// **************************************************************************

ArchiveOut _$ArchiveOutFromJson(Map<String, dynamic> json) =>
    ArchiveOut(result: ArchiveOutResult.fromJson(json['result'] as String));

Map<String, dynamic> _$ArchiveOutToJson(ArchiveOut instance) =>
    <String, dynamic>{'result': _$ArchiveOutResultEnumMap[instance.result]!};

const _$ArchiveOutResultEnumMap = {
  ArchiveOutResult.archived: 'archived',
  ArchiveOutResult.deleted: 'deleted',
  ArchiveOutResult.$unknown: r'$unknown',
};
