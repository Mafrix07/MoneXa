import 'dart:typed_data';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../data/upload_repository.dart';

// Events
abstract class UploadEvent {}

class UploadImageSubmittedEvent extends UploadEvent {
  final Uint8List imageBytes;
  final String filename;
  UploadImageSubmittedEvent({required this.imageBytes, required this.filename});
}

class UploadManualTextSubmittedEvent extends UploadEvent {
  final String text;
  UploadManualTextSubmittedEvent(this.text);
}

class ResetUploadEvent extends UploadEvent {}

// States
abstract class UploadState {}

class UploadInitial extends UploadState {}

class UploadProcessing extends UploadState {
  final String stepMessage;
  final int stepIndex; // 1 à 4
  UploadProcessing({required this.stepMessage, required this.stepIndex});
}

class UploadSuccess extends UploadState {
  final Map<String, dynamic> result;
  UploadSuccess(this.result);
}

class UploadFailure extends UploadState {
  final String message;
  UploadFailure(this.message);
}

// BLoC
class UploadBloc extends Bloc<UploadEvent, UploadState> {
  final UploadRepository _repository;

  UploadBloc({UploadRepository? repository})
      : _repository = repository ?? UploadRepository(),
        super(UploadInitial()) {
    on<UploadImageSubmittedEvent>((event, emit) async {
      emit(
        UploadProcessing(
          stepMessage: "Chargement de l'image du reçu...",
          stepIndex: 1,
        ),
      );

      await Future.delayed(const Duration(milliseconds: 300));
      emit(
        UploadProcessing(
          stepMessage: "Extraction multimodale par IA (Vision)...",
          stepIndex: 2,
        ),
      );

      try {
        final result = await _repository.uploadEvidence(
          imageBytes: event.imageBytes,
          filename: event.filename,
        );

        emit(
          UploadProcessing(
            stepMessage: "Validation Pydantic & Cascade de réconciliation...",
            stepIndex: 3,
          ),
        );
        await Future.delayed(const Duration(milliseconds: 300));

        emit(UploadSuccess(result));
      } catch (e) {
        emit(UploadFailure(e.toString().replaceAll("Exception: ", "")));
      }
    });

    on<UploadManualTextSubmittedEvent>((event, emit) async {
      emit(
        UploadProcessing(
          stepMessage: "Analyse du SMS texte brut (Plan B)...",
          stepIndex: 2,
        ),
      );
      try {
        final result = await _repository.uploadManualText(event.text);
        emit(UploadSuccess(result));
      } catch (e) {
        emit(UploadFailure(e.toString().replaceAll("Exception: ", "")));
      }
    });

    on<ResetUploadEvent>((event, emit) {
      emit(UploadInitial());
    });
  }
}
