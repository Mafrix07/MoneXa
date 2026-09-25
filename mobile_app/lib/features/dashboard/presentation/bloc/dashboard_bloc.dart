import 'package:flutter_bloc/flutter_bloc.dart';
import '../../data/dashboard_repository.dart';

// Events
abstract class DashboardEvent {}

class LoadDashboardEvent extends DashboardEvent {}

class RefreshDashboardEvent extends DashboardEvent {}

// States
abstract class DashboardState {}

class DashboardInitial extends DashboardState {}

class DashboardLoading extends DashboardState {}

class DashboardLoaded extends DashboardState {
  final DashboardData data;
  DashboardLoaded(this.data);
}

class DashboardError extends DashboardState {
  final String message;
  DashboardError(this.message);
}

// BLoC
class DashboardBloc extends Bloc<DashboardEvent, DashboardState> {
  final DashboardRepository _repository;

  DashboardBloc({DashboardRepository? repository})
      : _repository = repository ?? DashboardRepository(),
        super(DashboardInitial()) {
    on<LoadDashboardEvent>((event, emit) async {
      emit(DashboardLoading());
      try {
        final data = await _repository.getDashboardSummary();
        emit(DashboardLoaded(data));
      } catch (e) {
        emit(DashboardError(e.toString().replaceAll("Exception: ", "")));
      }
    });

    on<RefreshDashboardEvent>((event, emit) async {
      try {
        final data = await _repository.getDashboardSummary();
        emit(DashboardLoaded(data));
      } catch (e) {
        if (state is! DashboardLoaded) {
          emit(DashboardError(e.toString().replaceAll("Exception: ", "")));
        }
      }
    });
  }
}
