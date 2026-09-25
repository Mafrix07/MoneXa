"""Reporting serializers."""
from rest_framework import serializers


class KPISerializer(serializers.Serializer):
    """Serializer for the KPI bundle returned by /api/dashboard/summary/."""
    solde_total = serializers.FloatField()
    solde_par_canal = serializers.DictField(child=serializers.FloatField())
    encaisse_7j = serializers.FloatField()
    encaisse_30j = serializers.FloatField()
    decaisse_7j = serializers.FloatField()
    decaisse_30j = serializers.FloatField()
    flux_net_7j = serializers.FloatField()
    flux_net_30j = serializers.FloatField()
    factures_en_attente = serializers.IntegerField()
    factures_en_retard = serializers.IntegerField()
    paiements_a_valider = serializers.IntegerField()
    nb_anomalies = serializers.IntegerField()
    prevision_j7 = serializers.FloatField()
    prevision_j30 = serializers.FloatField()
    top_5_clients = serializers.ListField()
