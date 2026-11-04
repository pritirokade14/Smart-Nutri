// coverage:ignore-file
// GENERATED CODE - DO NOT MODIFY BY HAND
// ignore_for_file: type=lint, unused_import, invalid_annotation_target, unnecessary_import

import 'package:dio/dio.dart';
import 'package:retrofit/retrofit.dart';

import '../models/consent_in.dart';
import '../models/consent_state.dart';

part 'consents_client.g.dart';

@RestApi()
abstract class ConsentsClient {
  factory ConsentsClient(Dio dio, {String? baseUrl}) = _ConsentsClient;

  /// Consents List
  @GET('/v1/consents')
  Future<List<ConsentState>> consentsList();

  /// Consents Record
  @POST('/v1/consents')
  Future<List<ConsentState>> consentsRecord({@Body() required ConsentIn body});
}
