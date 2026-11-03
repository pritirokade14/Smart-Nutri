// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/member_in.dart';
import '../models/member_out.dart';
import '../models/member_patch.dart';

part 'members_client.g.dart';

@RestApi()
abstract class MembersClient {
  factory MembersClient(Dio dio, {String? baseUrl}) = _MembersClient;

  /// Members List.
  ///
  /// The account's members, the primary (account holder) first. Creates the primary if new.
  @GET('/v1/members')
  Future<List<MemberOut>> membersList();

  /// Members Create
  @POST('/v1/members')
  Future<MemberOut> membersCreate({@Body() required MemberIn body});

  /// Members Delete
  @DELETE('/v1/members/{member_id}')
  Future<void> membersDelete({@Path('member_id') required String memberId});

  /// Members Get
  @GET('/v1/members/{member_id}')
  Future<MemberOut> membersGet({@Path('member_id') required String memberId});

  /// Members Update
  @PATCH('/v1/members/{member_id}')
  Future<MemberOut> membersUpdate({
    @Path('member_id') required String memberId,
    @Body() required MemberPatch body,
  });
}
