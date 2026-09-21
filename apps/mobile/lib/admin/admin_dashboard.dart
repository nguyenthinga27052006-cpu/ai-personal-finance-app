import 'package:flutter/material.dart';
import '../auth/api_client.dart';
import '../components/sliding_tab_navigation.dart';
import '../settings/settings_controller.dart';

class AdminDashboardScreen extends StatefulWidget {
  const AdminDashboardScreen({
    super.key,
    required this.api,
    this.initialTabIndex = 0,
    this.showHeader = true,
  });

  final ApiClient api;
  final int initialTabIndex;
  final bool showHeader;

  static void open(BuildContext context, ApiClient api) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (context) => AdminDashboardScreen(api: api),
      ),
    );
  }

  @override
  State<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends State<AdminDashboardScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  bool _isLoadingStats = false;
  Map<String, dynamic>? _stats;

  // Users Tab State
  bool _isLoadingUsers = false;
  List<dynamic> _users = [];
  String _userSearchQuery = '';
  final _searchController = TextEditingController();

  // AI & Rate Limit Config State
  bool _isLoadingAIConfig = false;
  bool _isSavingAIConfig = false;
  String _selectedProvider = 'gemini';
  String _selectedModel = 'gemini-1.5-flash';
  final _apiKeyController = TextEditingController();
  bool _showApiKey = false;
  final _rpdController = TextEditingController(text: '1000');
  final _rpmController = TextEditingController(text: '60');
  final _tpmController = TextEditingController(text: '50000');

  @override
  void initState() {
    super.initState();
    final initial = widget.initialTabIndex.clamp(0, 2);
    _tabController = TabController(length: 3, vsync: this, initialIndex: initial);
    _loadStats();
    _loadUsers();
    _loadAIConfig();
  }

  @override
  void didUpdateWidget(AdminDashboardScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.initialTabIndex != oldWidget.initialTabIndex) {
      _tabController.animateTo(widget.initialTabIndex.clamp(0, 2));
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    _searchController.dispose();
    _apiKeyController.dispose();
    _rpdController.dispose();
    _rpmController.dispose();
    _tpmController.dispose();
    super.dispose();
  }

  Future<void> _loadStats() async {
    setState(() => _isLoadingStats = true);
    try {
      final res = await widget.api.getAdminStats();
      if (mounted) setState(() => _stats = res);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Tải thông số thất bại: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoadingStats = false);
    }
  }

  Future<void> _loadUsers() async {
    setState(() => _isLoadingUsers = true);
    try {
      final res = await widget.api.getAdminUsers(query: _userSearchQuery);
      if (mounted) {
        setState(() {
          _users = res['items'] as List<dynamic>? ?? [];
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Tải danh sách người dùng thất bại: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoadingUsers = false);
    }
  }

  Future<void> _loadAIConfig() async {
    setState(() => _isLoadingAIConfig = true);
    try {
      final res = await widget.api.getAIConfig();
      if (mounted) {
        setState(() {
          _selectedProvider = res['provider'] ?? 'gemini';
          _selectedModel = res['model_name'] ?? 'gemini-1.5-flash';
          _apiKeyController.text = res['api_key_masked'] ?? '';
          _rpdController.text = (res['rpd'] ?? 1000).toString();
          _rpmController.text = (res['rpm'] ?? 60).toString();
          _tpmController.text = (res['tpm'] ?? 50000).toString();
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Tải cấu hình AI thất bại: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isLoadingAIConfig = false);
    }
  }

  Future<void> _saveAIConfig() async {
    setState(() => _isSavingAIConfig = true);
    try {
      await widget.api.updateAIConfig(
        provider: _selectedProvider,
        modelName: _selectedModel,
        apiKey: _apiKeyController.text.trim(),
        rpd: int.tryParse(_rpdController.text.trim()) ?? 1000,
        rpm: int.tryParse(_rpmController.text.trim()) ?? 60,
        tpm: int.tryParse(_tpmController.text.trim()) ?? 50000,
      );
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Đã lưu cấu hình AI & Rate Limit thành công!')),
        );
        _loadAIConfig();
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lưu cấu hình thất bại: $e')),
        );
      }
    } finally {
      if (mounted) setState(() => _isSavingAIConfig = false);
    }
  }

  Future<void> _toggleUserStatus(Map<String, dynamic> user) async {
    final newStatus = user['status'] == 'ACTIVE' ? 'INACTIVE' : 'ACTIVE';
    try {
      await widget.api.updateAdminUserStatus(user['id'], newStatus);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Đã cập nhật trạng thái người dùng thành $newStatus')),
      );
      _loadUsers();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Cập nhật trạng thái thất bại: $e')),
      );
    }
  }

  Future<void> _toggleUserRole(Map<String, dynamic> user) async {
    final newRole = user['role'] == 'ADMIN' ? 'USER' : 'ADMIN';
    try {
      await widget.api.updateAdminUserRole(user['id'], newRole);
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Đã cập nhật vai trò người dùng thành $newRole')),
      );
      _loadUsers();
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Cập nhật vai trò thất bại: $e')),
      );
    }
  }

  Future<void> _resetUserPassword(Map<String, dynamic> user) async {
    final passController = TextEditingController();
    final result = await showDialog<bool>(
      context: context,
      builder: (dialogCtx) => AlertDialog(
        title: Text('Đặt lại mật khẩu cho ${user['email']}'),
        content: TextField(
          controller: passController,
          obscureText: true,
          decoration: const InputDecoration(
            labelText: 'Mật khẩu mới (tối thiểu 8 ký tự)',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogCtx, false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () => Navigator.pop(dialogCtx, true),
            child: const Text('Đổi mật khẩu'),
          ),
        ],
      ),
    );

    if (result == true) {
      final newPass = passController.text.trim();
      if (newPass.length < 8) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Mật khẩu phải có ít nhất 8 ký tự!')),
        );
        return;
      }
      try {
        await widget.api.resetAdminUserPassword(user['id'], newPass);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Đã đổi mật khẩu thành công cho ${user['email']}!')),
        );
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Lỗi đổi mật khẩu: $e')),
        );
      }
    }
  }

  Future<void> _viewUserDetail(Map<String, dynamic> user) async {
    showDialog(
      context: context,
      builder: (ctx) => FutureBuilder<Map<String, dynamic>>(
        future: widget.api.getAdminUserDetail(user['id']),
        builder: (context, snapshot) {
          if (snapshot.connectionState == ConnectionState.waiting) {
            return const AlertDialog(
              content: SizedBox(
                height: 100,
                child: Center(child: CircularProgressIndicator()),
              ),
            );
          }
          if (snapshot.hasError) {
            return AlertDialog(
              title: const Text('Lỗi'),
              content: Text('${snapshot.error}'),
              actions: [
                TextButton(
                  onPressed: () => Navigator.pop(ctx),
                  child: const Text('Đóng'),
                )
              ],
            );
          }
          final detail = snapshot.data!;
          final stats = detail['stats'] as Map<String, dynamic>? ?? {};
          return AlertDialog(
            title: Text('Thông tin: ${detail['email']}'),
            content: SingleChildScrollView(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('ID: ${detail['id']}'),
                  Text('Tên: ${detail['display_name'] ?? "Chưa đặt"}'),
                  Text('Vai trò: ${detail['role']}'),
                  Text('Trạng thái: ${detail['status']}'),
                  Text('Ngày tạo: ${detail['created_at']}'),
                  const Divider(height: 24),
                  const Text('Dữ liệu tài chính:', style: TextStyle(fontWeight: FontWeight.bold)),
                  Text('• Số lượng Tài khoản: ${stats['accounts'] ?? 0}'),
                  Text('• Số lượng Giao dịch: ${stats['transactions'] ?? 0}'),
                  Text('• Số lượng Ngân sách: ${stats['budgets'] ?? 0}'),
                  Text('• Số lượng Mục tiêu: ${stats['goals'] ?? 0}'),
                ],
              ),
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.pop(ctx),
                child: const Text('Đóng'),
              ),
            ],
          );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final settings = InheritedSettings.of(context);
    final tabBar = SlidingIndicatorTabBar(
      controller: _tabController,
      tabs: const [
        Tab(icon: Icon(Icons.dashboard), text: 'Tổng quan & Biểu đồ'),
        Tab(icon: Icon(Icons.people), text: 'Người dùng & Phân quyền'),
        Tab(icon: Icon(Icons.psychology), text: 'AI & Rate Limit'),
      ],
    );

    final content = TabBarView(
      controller: _tabController,
      children: [
        _buildStatsTab(settings),
        _buildUsersTab(settings),
        _buildAIConfigTab(settings),
      ],
    );

    if (!widget.showHeader) {
      return Column(
        children: [
          Container(
            color: Theme.of(context).canvasColor,
            child: tabBar,
          ),
          const Divider(height: 1),
          Expanded(child: content),
        ],
      );
    }

    return Scaffold(
      appBar: AppBar(
        title: const Row(
          children: [
            Icon(Icons.admin_panel_settings, color: Colors.amber),
            SizedBox(width: 8),
            Text('Trình Quản Lý Admin (Admin Portal)'),
          ],
        ),
        bottom: tabBar,
      ),
      body: content,
    );
  }

  Widget _buildStatsTab(SettingsController settings) {
    if (_isLoadingStats) {
      return const Center(child: CircularProgressIndicator());
    }
    final totalUsers = _stats?['total_users'] as int? ?? 0;
    final activeUsers = _stats?['active_users'] as int? ?? 0;
    final totalTx = _stats?['total_transactions'] as int? ?? 0;
    final totalChat = _stats?['total_chat_messages'] as int? ?? 0;
    final vectorChunks = _stats?['vector_store_chunks'] as int? ?? 0;

    return RefreshIndicator(
      onRefresh: _loadStats,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Text(
            'Báo cáo & Phân Tích Dữ Liệu Hệ Thống Realtime',
            style: Theme.of(context).textTheme.titleLarge?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 16),
          GridView.count(
            crossAxisCount: MediaQuery.of(context).size.width > 600 ? 4 : 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            children: [
              _buildStatCard('Tổng người dùng', '$totalUsers', Icons.people, Colors.blue),
              _buildStatCard('Đang hoạt động', '$activeUsers', Icons.check_circle, Colors.green),
              _buildStatCard('Tổng giao dịch', '$totalTx', Icons.receipt_long, Colors.teal),
              _buildStatCard('Lượt hỏi AI', '$totalChat', Icons.chat, Colors.purple),
            ],
          ),
          const SizedBox(height: 24),
          // Biểu đồ 1: Phân bố & Trạng thái Người dùng
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.pie_chart, color: Colors.blue),
                      SizedBox(width: 8),
                      Text(
                        'Biểu Đồ Phân Bổ Trạng Thái Người Dùng',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                const Text('Tỷ lệ Người dùng Hoạt động (Active)', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
                                Text('${totalUsers > 0 ? ((activeUsers / totalUsers) * 100).toStringAsFixed(1) : 100}%', style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.green)),
                              ],
                            ),
                            const SizedBox(height: 6),
                            LinearProgressIndicator(
                              value: totalUsers > 0 ? (activeUsers / totalUsers) : 1.0,
                              backgroundColor: Colors.red.shade100,
                              color: Colors.green,
                              minHeight: 12,
                              borderRadius: BorderRadius.circular(6),
                            ),
                            const SizedBox(height: 8),
                            Text(
                              '• Active: $activeUsers người dùng | • Inactive/Blocked: ${totalUsers - activeUsers} người dùng',
                              style: const TextStyle(fontSize: 12, color: Colors.grey),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          // Biểu đồ 2: Tải Hệ thống & AI Rate Limits
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.speed, color: Colors.purple),
                      SizedBox(width: 8),
                      Text(
                        'Tải Hệ Thống & Hạn Mức AI Quotas (Rate Limits)',
                        style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  _buildQuotaBar('RPD (Requests Per Day)', '$totalChat / ${int.tryParse(_rpdController.text) ?? 1000} requests', Colors.purple, totalChat / (int.tryParse(_rpdController.text) ?? 1000)),
                  const SizedBox(height: 12),
                  _buildQuotaBar('RPM (Requests Per Minute)', 'Hoạt động bình thường (Hạn mức ${int.tryParse(_rpmController.text) ?? 60} req/min)', Colors.teal, 0.15),
                  const SizedBox(height: 12),
                  _buildQuotaBar('TPM (Tokens Per Minute)', 'Tải ổn định (Giới hạn ${int.tryParse(_tpmController.text) ?? 50000} tokens/min)', Colors.indigo, 0.20),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),
          Card(
            elevation: 2,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            child: ListTile(
              leading: const CircleAvatar(
                backgroundColor: Colors.indigoAccent,
                child: Icon(Icons.storage, color: Colors.white),
              ),
              title: const Text('RAG Knowledge Vector Store', style: TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text('Số lượng Knowledge Chunks đã index vào Vector Database: $vectorChunks chunks'),
              trailing: const Chip(label: Text('Sẵn sàng'), backgroundColor: Colors.greenAccent),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuotaBar(String title, String subtitle, Color color, double progress) {
    final clamped = progress.clamp(0.0, 1.0);
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13)),
            Text(subtitle, style: TextStyle(fontSize: 12, color: color, fontWeight: FontWeight.w600)),
          ],
        ),
        const SizedBox(height: 6),
        LinearProgressIndicator(
          value: clamped,
          backgroundColor: Colors.grey.shade200,
          color: color,
          minHeight: 8,
          borderRadius: BorderRadius.circular(4),
        ),
      ],
    );
  }

  Widget _buildStatCard(String label, String value, IconData icon, Color color) {
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 32, color: color),
            const SizedBox(height: 8),
            Text(value, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(label, style: const TextStyle(fontSize: 12, color: Colors.grey), textAlign: TextAlign.center),
          ],
        ),
      ),
    );
  }

  Widget _buildUsersTab(SettingsController settings) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(12),
          child: TextField(
            controller: _searchController,
            decoration: InputDecoration(
              hintText: 'Tìm kiếm người dùng theo Email / Tên...',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: IconButton(
                icon: const Icon(Icons.clear),
                onPressed: () {
                  _searchController.clear();
                  _userSearchQuery = '';
                  _loadUsers();
                },
              ),
              border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
            ),
            onSubmitted: (val) {
              _userSearchQuery = val.trim();
              _loadUsers();
            },
          ),
        ),
        Expanded(
          child: _isLoadingUsers
              ? const Center(child: CircularProgressIndicator())
              : RefreshIndicator(
                  onRefresh: _loadUsers,
                  child: ListView.builder(
                    itemCount: _users.length,
                    itemBuilder: (context, index) {
                      final u = _users[index] as Map<String, dynamic>;
                      final role = u['role'] ?? 'USER';
                      final status = u['status'] ?? 'ACTIVE';
                      final isAdmin = role == 'ADMIN';
                      final isActive = status == 'ACTIVE';

                      return Card(
                        margin: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
                        child: ListTile(
                          leading: CircleAvatar(
                            backgroundColor: isAdmin ? Colors.amber.shade100 : Colors.teal.shade100,
                            child: Icon(
                              isAdmin ? Icons.admin_panel_settings : Icons.person,
                              color: isAdmin ? Colors.amber.shade900 : Colors.teal,
                            ),
                          ),
                          title: Text(
                            u['email'] ?? '',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          subtitle: Text('Tên: ${u['display_name'] ?? 'N/A'} • Đăng ký: ${u['created_at'].toString().split('T').first}'),
                          trailing: PopupMenuButton<String>(
                            icon: const Icon(Icons.more_vert),
                            onSelected: (val) {
                              if (val == 'detail') _viewUserDetail(u);
                              if (val == 'toggle_status') _toggleUserStatus(u);
                              if (val == 'toggle_role') _toggleUserRole(u);
                              if (val == 'reset_password') _resetUserPassword(u);
                              if (val == 'delete_user') _deleteUserByAdmin(u);
                            },
                            itemBuilder: (ctx) => [
                              const PopupMenuItem(
                                value: 'detail',
                                child: Row(
                                  children: [
                                    Icon(Icons.info_outline, size: 18),
                                    SizedBox(width: 8),
                                    Text('Xem chi tiết'),
                                  ],
                                ),
                              ),
                              PopupMenuItem(
                                value: 'toggle_status',
                                child: Row(
                                  children: [
                                    Icon(isActive ? Icons.block : Icons.check_circle, color: isActive ? Colors.red : Colors.green, size: 18),
                                    const SizedBox(width: 8),
                                    Text(isActive ? 'Khóa tài khoản' : 'Mở khóa tài khoản'),
                                  ],
                                ),
                              ),
                              PopupMenuItem(
                                value: 'toggle_role',
                                child: Row(
                                  children: [
                                    Icon(isAdmin ? Icons.person : Icons.admin_panel_settings, color: Colors.blue, size: 18),
                                    const SizedBox(width: 8),
                                    Text(isAdmin ? 'Chuyển về USER' : 'Nâng cấp ADMIN'),
                                  ],
                                ),
                              ),
                              const PopupMenuItem(
                                value: 'reset_password',
                                child: Row(
                                  children: [
                                    Icon(Icons.lock_reset, color: Colors.orange, size: 18),
                                    SizedBox(width: 8),
                                    Text('Đặt lại mật khẩu'),
                                  ],
                                ),
                              ),
                              if (u['email'] != 'admin@finance.app')
                                const PopupMenuItem(
                                  value: 'delete_user',
                                  child: Row(
                                    children: [
                                      Icon(Icons.delete_forever, color: Colors.red, size: 18),
                                      SizedBox(width: 8),
                                      Text('Xóa người dùng', style: TextStyle(color: Colors.red)),
                                    ],
                                  ),
                                ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
        ),
      ],
    );
  }

  Future<void> _deleteUserByAdmin(Map<String, dynamic> user) async {
    if (user['email'] == 'admin@finance.app') {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Không thể xóa tài khoản Super Admin hệ thống!')),
      );
      return;
    }
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: Text('Xóa tài khoản ${user['email']}'),
        content: const Text('Bạn có chắc chắn muốn XÓA VĨNH VIỄN người dùng này và tất cả dữ liệu liên quan không?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Hủy'),
          ),
          FilledButton(
            style: FilledButton.styleFrom(backgroundColor: Colors.red),
            onPressed: () => Navigator.pop(ctx, true),
            child: const Text('Xóa người dùng'),
          ),
        ],
      ),
    );

    if (confirm == true) {
      try {
        await widget.api.deleteAdminUser(user['id']);
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Đã xóa thành công tài khoản ${user['email']}')),
          );
          _loadUsers();
        }
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Lỗi xóa người dùng: $e')),
          );
        }
      }
    }
  }

  Widget _buildAIConfigTab(SettingsController settings) {
    if (_isLoadingAIConfig) {
      return const Center(child: CircularProgressIndicator());
    }

    final providers = [
      {'id': 'gemini', 'name': 'Google Gemini AI'},
      {'id': 'openai', 'name': 'OpenAI GPT'},
      {'id': 'anthropic', 'name': 'Anthropic Claude'},
      {'id': 'custom', 'name': 'Custom Local LLM'},
    ];

    final modelsMap = {
      'gemini': ['gemini-3.1-flash-lite', 'gemini-2.0-flash', 'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro'],
      'openai': ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
      'anthropic': ['claude-3-5-sonnet', 'claude-3-haiku', 'claude-3-opus'],
      'custom': ['local-model-default'],
    };

    final availableModels = modelsMap[_selectedProvider] ?? ['gemini-1.5-flash'];

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Cấu hình Nhà cung cấp AI (Provider & Model)',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          DropdownButtonFormField<String>(
            value: _selectedProvider,
            decoration: const InputDecoration(
              labelText: 'AI Provider',
              border: OutlineInputBorder(),
            ),
            items: providers
                .map((p) => DropdownMenuItem(value: p['id'], child: Text(p['name']!)))
                .toList(),
            onChanged: (val) {
              if (val != null) {
                setState(() {
                  _selectedProvider = val;
                  _selectedModel = (modelsMap[val] ?? ['default']).first;
                });
              }
            },
          ),
          const SizedBox(height: 16),
          DropdownButtonFormField<String>(
            value: availableModels.contains(_selectedModel) ? _selectedModel : availableModels.first,
            decoration: const InputDecoration(
              labelText: 'Mô hình AI (Model)',
              border: OutlineInputBorder(),
            ),
            items: availableModels
                .map((m) => DropdownMenuItem(value: m, child: Text(m)))
                .toList(),
            onChanged: (val) {
              if (val != null) setState(() => _selectedModel = val);
            },
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _apiKeyController,
            obscureText: !_showApiKey,
            decoration: InputDecoration(
              labelText: 'API Key (Quản lý Khóa API)',
              border: const OutlineInputBorder(),
              suffixIcon: IconButton(
                icon: Icon(_showApiKey ? Icons.visibility_off : Icons.visibility),
                onPressed: () => setState(() => _showApiKey = !_showApiKey),
              ),
            ),
          ),
          const SizedBox(height: 24),
          Text(
            'Quản lý Rate Limits & Quotas (RPD / RPM / TPM)',
            style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold),
          ),
          const SizedBox(height: 12),
          TextField(
            controller: _rpdController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'RPD (Requests Per Day - Số yêu cầu tối đa / ngày)',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _rpmController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'RPM (Requests Per Minute - Số yêu cầu tối đa / phút)',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            controller: _tpmController,
            keyboardType: TextInputType.number,
            decoration: const InputDecoration(
              labelText: 'TPM (Tokens Per Minute - Giới hạn Tokens / phút)',
              border: OutlineInputBorder(),
            ),
          ),
          const SizedBox(height: 24),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: FilledButton.icon(
              icon: _isSavingAIConfig
                  ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.save),
              label: Text(_isSavingAIConfig ? 'Đang lưu...' : 'Lưu Cấu Hình AI & Quotas'),
              onPressed: _isSavingAIConfig ? null : _saveAIConfig,
            ),
          ),
        ],
      ),
    );
  }
}
