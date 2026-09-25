import 'package:hive/hive.dart';
import '../../../core/constants/app_constants.dart';
import '../../../core/network/api_client.dart';
import '../../../core/network/api_endpoints.dart';

class DashboardData {
  final double soldeTotal;
  final Map<String, double> soldeParCanal;
  final double encaisse7j;
  final double decaisse7j;
  final double fluxNet7j;
  final double encaisse30j;
  final double decaisse30j;
  final double fluxNet30j;
  final int facturesEnRetard;
  final int facturesEnAttente;
  final int paiementsAValider;
  final int anomaliesNonResolues;
  final List<dynamic> topClients;
  final bool isFromCache;

  DashboardData({
    required this.soldeTotal,
    required this.soldeParCanal,
    required this.encaisse7j,
    required this.decaisse7j,
    required this.fluxNet7j,
    required this.encaisse30j,
    required this.decaisse30j,
    required this.fluxNet30j,
    required this.facturesEnRetard,
    required this.facturesEnAttente,
    required this.paiementsAValider,
    required this.anomaliesNonResolues,
    required this.topClients,
    this.isFromCache = false,
  });

  factory DashboardData.fromJson(Map<String, dynamic> json, {bool isFromCache = false}) {
    final rawCanal = json['solde_par_canal'] as Map<String, dynamic>? ?? {};
    final convertedCanal = <String, double>{};
    rawCanal.forEach((k, v) {
      convertedCanal[k] = (v as num?)?.toDouble() ?? 0.0;
    });

    return DashboardData(
      soldeTotal: (json['solde_total'] as num?)?.toDouble() ?? 0.0,
      soldeParCanal: convertedCanal,
      encaisse7j: (json['encaisse_7j'] as num?)?.toDouble() ?? 0.0,
      decaisse7j: (json['decaisse_7j'] as num?)?.toDouble() ?? 0.0,
      fluxNet7j: (json['flux_net_7j'] as num?)?.toDouble() ?? 0.0,
      encaisse30j: (json['encaisse_30j'] as num?)?.toDouble() ?? 0.0,
      decaisse30j: (json['decaisse_30j'] as num?)?.toDouble() ?? 0.0,
      fluxNet30j: (json['flux_net_30j'] as num?)?.toDouble() ?? 0.0,
      facturesEnRetard: json['factures_en_retard'] ?? 0,
      facturesEnAttente: json['factures_en_attente'] ?? 0,
      paiementsAValider: json['paiements_a_valider'] ?? 0,
      anomaliesNonResolues: json['anomalies_non_resolues'] ?? 0,
      topClients: json['top_5_clients'] ?? [],
      isFromCache: isFromCache,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'solde_total': soldeTotal,
      'solde_par_canal': soldeParCanal,
      'encaisse_7j': encaisse7j,
      'decaisse_7j': decaisse7j,
      'flux_net_7j': fluxNet7j,
      'encaisse_30j': encaisse30j,
      'decaisse_30j': decaisse30j,
      'flux_net_30j': fluxNet30j,
      'factures_en_retard': facturesEnRetard,
      'factures_en_attente': facturesEnAttente,
      'paiements_a_valider': paiementsAValider,
      'anomalies_non_resolues': anomaliesNonResolues,
      'top_5_clients': topClients,
    };
  }
}

class DashboardRepository {
  final ApiClient _client = ApiClient();

  Future<DashboardData> getDashboardSummary() async {
    final box = Hive.isBoxOpen(AppConstants.kpiBoxName)
        ? Hive.box(AppConstants.kpiBoxName)
        : await Hive.openBox(AppConstants.kpiBoxName);

    try {
      final response = await _client.dio.get(ApiEndpoints.dashboardSummary);
      final dataMap = Map<String, dynamic>.from(response.data);

      // Mise en cache Hive
      await box.put('summary', dataMap);

      return DashboardData.fromJson(dataMap, isFromCache: false);
    } catch (_) {
      // Stratégie Offline-First : charger depuis le cache Hive si indisponible
      final cached = box.get('summary');
      if (cached != null) {
        return DashboardData.fromJson(
          Map<String, dynamic>.from(cached),
          isFromCache: true,
        );
      }

      // Données démo offline par défaut (Cahier des charges Hackathon)
      final defaultDemo = <String, dynamic>{
        'solde_total': 4850000.0,
        'solde_par_canal': {
          'TMONEY': 2150000.0,
          'MOOV': 1800000.0,
          'FLOOZ': 900000.0,
        },
        'encaisse_7j': 1450000.0,
        'decaisse_7j': 620000.0,
        'flux_net_7j': 830000.0,
        'encaisse_30j': 6200000.0,
        'decaisse_30j': 3100000.0,
        'flux_net_30j': 3100000.0,
        'factures_en_retard': 4,
        'factures_en_attente': 12,
        'paiements_a_valider': 3,
        'anomalies_non_resolues': 2,
        'top_5_clients': [
          {'client_name': 'Ets Kossi & Frères', 'total_amount': 1250000.0},
          {'client_name': 'Pharmacie du Grand Marché', 'total_amount': 980000.0},
          {'client_name': 'Boutique Mensah SARL', 'total_amount': 720000.0},
        ],
      };
      await box.put('summary', defaultDemo);
      return DashboardData.fromJson(defaultDemo, isFromCache: true);
    }
  }
}
