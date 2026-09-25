import 'dart:typed_data';
import 'package:flutter_test/flutter_test.dart';
import 'package:monexa/features/upload_evidence/data/upload_repository.dart';
import 'package:monexa/features/upload_evidence/presentation/bloc/upload_bloc.dart';

class FakeUploadRepository extends UploadRepository {
  bool shouldFail = false;
  Map<String, dynamic>? mockResult;

  @override
  Future<Map<String, dynamic>> uploadEvidence({
    required Uint8List imageBytes,
    required String filename,
  }) async {
    if (shouldFail) {
      throw Exception('Erreur de traitement image');
    }
    return mockResult ??
        {
          'id': 101,
          'amount': 50000.0,
          'channel': 'TMONEY',
          'provider_ref': 'TMX98234710',
          'payer_name': 'Kossi Mensah',
          'ai_confidence': 0.98,
          'status': 'A_VALIDER',
        };
  }

  @override
  Future<Map<String, dynamic>> uploadManualText(String text) async {
    if (shouldFail) {
      throw Exception('Erreur de traitement texte SMS');
    }
    return mockResult ??
        {
          'id': 102,
          'amount': 120000.0,
          'channel': 'MOOV',
          'provider_ref': 'MV8820311',
          'payer_name': 'Afi Adjovi',
          'ai_confidence': 0.95,
          'status': 'A_VALIDER',
        };
  }
}

void main() {
  group('UploadBloc tests', () {
    late FakeUploadRepository fakeRepo;
    late UploadBloc uploadBloc;

    setUp(() {
      fakeRepo = FakeUploadRepository();
      uploadBloc = UploadBloc(repository: fakeRepo);
    });

    tearDown(() {
      uploadBloc.close();
    });

    test('Initial state is UploadInitial', () {
      expect(uploadBloc.state, isA<UploadInitial>());
    });

    test('UploadImageSubmittedEvent emits processing steps then UploadSuccess', () async {
      uploadBloc.add(
        UploadImageSubmittedEvent(
          imageBytes: Uint8List.fromList([1, 2, 3, 4]),
          filename: 'receipt.jpg',
        ),
      );

      await expectLater(
        uploadBloc.stream,
        emitsInOrder([
          isA<UploadProcessing>(),
          isA<UploadProcessing>(),
          isA<UploadProcessing>(),
          predicate<UploadState>((state) {
            return state is UploadSuccess &&
                state.result['amount'] == 50000.0 &&
                state.result['provider_ref'] == 'TMX98234710';
          }),
        ]),
      );
    });

    test('UploadManualTextSubmittedEvent emits processing then UploadSuccess', () async {
      uploadBloc.add(
        UploadManualTextSubmittedEvent('Paiement Moov 120000 FCFA'),
      );

      await expectLater(
        uploadBloc.stream,
        emitsInOrder([
          isA<UploadProcessing>(),
          predicate<UploadState>((state) {
            return state is UploadSuccess &&
                state.result['amount'] == 120000.0 &&
                state.result['channel'] == 'MOOV';
          }),
        ]),
      );
    });

    test('ResetUploadEvent emits UploadInitial', () async {
      uploadBloc.add(ResetUploadEvent());

      await expectLater(
        uploadBloc.stream,
        emitsInOrder([
          isA<UploadInitial>(),
        ]),
      );
    });
  });
}
