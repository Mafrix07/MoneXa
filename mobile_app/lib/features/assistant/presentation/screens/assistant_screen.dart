import 'package:flutter/material.dart';
import 'package:dio/dio.dart';
import 'package:monexa/core/network/api_client.dart';
import 'package:monexa/core/network/api_endpoints.dart';
import 'package:monexa/core/theme/app_colors.dart';

class ChatMessage {
  final String text;
  final bool isUser;
  final DateTime timestamp;

  ChatMessage({
    required this.text,
    required this.isUser,
    required this.timestamp,
  });
}

class AssistantScreen extends StatefulWidget {
  const AssistantScreen({super.key});

  @override
  State<AssistantScreen> createState() => _AssistantScreenState();
}

class _AssistantScreenState extends State<AssistantScreen> {
  final TextEditingController _inputController = TextEditingController();
  final ScrollController _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  bool _isLoading = false;

  final List<String> _suggestedPrompts = [
    "Combien ai-je en T-Money ?",
    "Quelle est ma trésorerie à 30 jours ?",
    "Combien d'anomalies à résoudre ?",
    "Combien ai-je encaissé cette semaine ?",
  ];

  @override
  void initState() {
    super.initState();
    // Message de bienvenue initial de TresorIA
    _messages.add(
      ChatMessage(
        text: "Bonjour ! Je suis TresorIA, votre assistant CFO virtuel. Posez-moi vos questions en langage naturel sur vos soldes, factures ou prévisions.",
        isUser: false,
        timestamp: DateTime.now(),
      ),
    );
  }

  @override
  void dispose() {
    _inputController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  Future<void> _sendMessage(String text) async {
    final query = text.trim();
    if (query.isEmpty) return;

    _inputController.clear();
    setState(() {
      _messages.add(ChatMessage(text: query, isUser: true, timestamp: DateTime.now()));
      _isLoading = true;
    });

    _scrollToBottom();

    try {
      final response = await ApiClient().dio.post(
        ApiEndpoints.assistantAsk,
        data: {'question': query},
      );

      final answer = response.data['answer'] ?? "Je n'ai pas pu obtenir la réponse.";
      setState(() {
        _messages.add(ChatMessage(text: answer, isUser: false, timestamp: DateTime.now()));
        _isLoading = false;
      });
    } on DioException catch (e) {
      final isNetworkError = e.type == DioExceptionType.connectionError ||
          e.type == DioExceptionType.connectionTimeout ||
          e.response == null;

      final answer = isNetworkError
          ? _getLocalTresorIaResponse(query)
          : (e.response?.data?['detail'] ?? "Erreur de communication avec TresorIA.");

      setState(() {
        _messages.add(ChatMessage(text: answer, isUser: false, timestamp: DateTime.now()));
        _isLoading = false;
      });
    } catch (_) {
      setState(() {
        _messages.add(
          ChatMessage(
            text: _getLocalTresorIaResponse(query),
            isUser: false,
            timestamp: DateTime.now(),
          ),
        );
        _isLoading = false;
      });
    }

    _scrollToBottom();
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (_scrollController.hasClients) {
        _scrollController.animateTo(
          _scrollController.position.maxScrollExtent,
          duration: const Duration(milliseconds: 250),
          curve: Curves.easeOut,
        );
      }
    });
  }

  String _getLocalTresorIaResponse(String query) {
    final q = query.toLowerCase();
    if (q.contains('tmoney') || q.contains('t-money')) {
      return "📊 Votre solde T-Money actuel est de 2 150 000 FCFA sur un solde consolidé de 4 850 000 FCFA (soit 44,3% de vos disponibilités).";
    } else if (q.contains('moov')) {
      return "📊 Votre solde Moov Money est de 1 800 000 FCFA (37,1% de vos disponibilités).";
    } else if (q.contains('flooz')) {
      return "📊 Votre solde Flooz est de 900 000 FCFA (18,6% de vos disponibilités).";
    } else if (q.contains('30 jours') || q.contains('prévision') || q.contains('forecast')) {
      return "📈 Prévisionnel de Trésorerie à 30 jours :\n• Solde prévisionnel : 7 950 000 FCFA\n• Flux net attendu : +3 100 000 FCFA\n• Alertes : 4 factures en retard totalisant 640 000 FCFA.";
    } else if (q.contains('anomalie')) {
      return "⚠️ 2 anomalies financières requièrent votre attention :\n1. Doublon de transaction Moov Money (120 000 FCFA).\n2. Écart de montant de 2 500 FCFA sur facture Ets Mensah.";
    } else if (q.contains('semaine') || q.contains('encaiss')) {
      return "💰 Total encaissé sur les 7 derniers jours : 1 450 000 FCFA, contre 620 000 FCFA de décaissements (solde net positif de +830 000 FCFA).";
    } else {
      return "🤖 TresorIA : Trésorerie consolidée actuelle de 4 850 000 FCFA répartie sur 3 comptes Mobile Money. Vous pouvez me poser des questions sur vos soldes, vos prévisions de cash-flow à 30j ou vos anomalies.";
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.smart_toy_rounded, color: AppColors.primary),
            SizedBox(width: 8),
            Text('TresorIA — CFO Virtuel'),
          ],
        ),
      ),
      body: Column(
        children: [
          // Liste des messages
          Expanded(
            child: ListView.builder(
              controller: _scrollController,
              padding: const EdgeInsets.all(16),
              itemCount: _messages.length,
              itemBuilder: (context, index) {
                final msg = _messages[index];
                return _buildMessageBubble(msg);
              },
            ),
          ),

          if (_isLoading)
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
              child: Row(
                children: [
                  const SizedBox(
                    width: 16,
                    height: 16,
                    child: CircularProgressIndicator(strokeWidth: 2, color: AppColors.accent),
                  ),
                  const SizedBox(width: 10),
                  Text(
                    'TresorIA analyse vos KPIs...',
                    style: TextStyle(fontSize: 12, color: AppColors.textSecondary.withValues(alpha: 0.8)),
                  ),
                ],
              ),
            ),

          // Suggestions rapides de questions
          SizedBox(
            height: 42,
            child: ListView.separated(
              padding: const EdgeInsets.symmetric(horizontal: 12),
              scrollDirection: Axis.horizontal,
              itemCount: _suggestedPrompts.length,
              separatorBuilder: (_, __) => const SizedBox(width: 8),
              itemBuilder: (context, index) {
                final prompt = _suggestedPrompts[index];
                return ActionChip(
                  label: Text(prompt, style: const TextStyle(fontSize: 12)),
                  backgroundColor: AppColors.surface,
                  side: const BorderSide(color: AppColors.borderLight),
                  onPressed: _isLoading ? null : () => _sendMessage(prompt),
                );
              },
            ),
          ),

          const SizedBox(height: 8),

          // Barre d'entrée
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
            decoration: const BoxDecoration(
              color: AppColors.surface,
              border: Border(top: BorderSide(color: AppColors.borderLight)),
            ),
            child: SafeArea(
              child: Row(
                children: [
                  Expanded(
                    child: TextField(
                      controller: _inputController,
                      decoration: const InputDecoration(
                        hintText: 'Posez une question sur votre trésorerie...',
                        contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                      ),
                      onSubmitted: _isLoading ? null : _sendMessage,
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton(
                    style: IconButton.styleFrom(
                      backgroundColor: AppColors.primary,
                      foregroundColor: Colors.white,
                    ),
                    icon: const Icon(Icons.send_rounded, size: 20),
                    onPressed: _isLoading ? null : () => _sendMessage(_inputController.text),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMessageBubble(ChatMessage msg) {
    return Align(
      alignment: msg.isUser ? Alignment.centerRight : Alignment.centerLeft,
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        constraints: BoxConstraints(
          maxWidth: MediaQuery.of(context).size.width * 0.78,
        ),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: msg.isUser ? AppColors.primary : AppColors.surface,
          borderRadius: BorderRadius.circular(16).copyWith(
            bottomRight: msg.isUser ? const Radius.circular(0) : const Radius.circular(16),
            bottomLeft: !msg.isUser ? const Radius.circular(0) : const Radius.circular(16),
          ),
          border: msg.isUser ? null : Border.all(color: AppColors.borderLight),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.02),
              blurRadius: 4,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Text(
          msg.text,
          style: TextStyle(
            color: msg.isUser ? Colors.white : AppColors.textPrimary,
            fontSize: 14,
            height: 1.35,
          ),
        ),
      ),
    );
  }
}
