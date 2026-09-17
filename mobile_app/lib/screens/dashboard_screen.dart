import 'package:flutter/material.dart';
import 'package:supabase_flutter/supabase_flutter.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({Key? key}) : super(key: key);

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  final SupabaseClient supabase = Supabase.instance.client;
  double _hardwareRevenue = 0.0;
  double _mediaRevenue = 0.0;
  double _totalProfit = 0.0;
  List<Map<String, dynamic>> _recentSales = [];

  @override
  void initState() {
    super.initState();
    _fetchDashboardData();
    _subscribeToLiveSales();
  }

  void _fetchDashboardData() async {
    try {
      final response = await supabase
          .from('sales')
          .select()
          .order('created_at', ascending: false)
          .limit(20);

      double hw = 0.0;
      double media = 0.0;
      double profit = 0.0;
      final list = List<Map<String, dynamic>>.from(response);

      for (var item in list) {
        hw += (item['hardware_revenue'] as num? ?? 0.0).toDouble();
        media += (item['media_service_revenue'] as num? ?? 0.0).toDouble();
        profit += (item['total_profit'] as num? ?? 0.0).toDouble();
      }

      setState(() {
        _hardwareRevenue = hw;
        _mediaRevenue = media;
        _totalProfit = profit;
        _recentSales = list;
      });
    } catch (e) {
      // Offline fallback state
    }
  }

  void _subscribeToLiveSales() {
    supabase.channel('public:sales').onPostgresChanges(
      event: PostgresChangeEvent.insert,
      schema: 'public',
      table: 'sales',
      callback: (payload) {
        _fetchDashboardData();
      },
    ).subscribe();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFF121824),
      appBar: AppBar(
        backgroundColor: const Color(0xFF1E293B),
        title: const Text("ElectroStore Mobile Dashboard", style: TextStyle(fontSize: 18, color: Colors.white, fontWeight: FontWeight.bold)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh, color: Color(0xFF38BDF8)),
            onPressed: _fetchDashboardData,
          )
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Revenue Split Metrics
            Row(
              children: [
                Expanded(
                  child: _buildMetricCard("Hardware Sales", "PKR ${_hardwareRevenue.toStringAsFixed(0)}", const Color(0xFF0284C7), Icons.inventory_2),
                ),
                const SizedBox(width: 8),
                Expanded(
                  child: _buildMetricCard("USB Media Copying", "PKR ${_mediaRevenue.toStringAsFixed(0)}", const Color(0xFF059669), Icons.movie),
                ),
              ],
            ),
            const SizedBox(height: 8),
            _buildMetricCard("Overall Net Profit", "PKR ${_totalProfit.toStringAsFixed(0)}", const Color(0xFF7C3AED), Icons.trending_up),
            
            const SizedBox(height: 24),
            const Text(
              "Live Sales Stream (Real-Time)",
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold, color: Colors.white),
            ),
            const SizedBox(height: 12),
            _recentSales.isEmpty
                ? const Center(child: Padding(
                    padding: EdgeInsets.all(24.0),
                    child: Text("No sales recorded today yet", style: TextStyle(color: Colors.grey)),
                  ))
                : ListView.builder(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: _recentSales.length,
                    itemBuilder: (context, index) {
                      final sale = _recentSales[index];
                      final double hwRev = (sale['hardware_revenue'] as num? ?? 0.0).toDouble();
                      final double mediaRev = (sale['media_service_revenue'] as num? ?? 0.0).toDouble();

                      return Card(
                        color: const Color(0xFF1E293B),
                        margin: const EdgeInsets.only(bottom: 8.0),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        child: ListTile(
                          leading: const CircleAvatar(
                            backgroundColor: Color(0xFF0284C7),
                            child: Icon(Icons.receipt_long, color: Colors.white, size: 20),
                          ),
                          title: Text(
                            "Invoice #${sale['receipt_number']}",
                            style: const TextStyle(fontWeight: FontWeight.bold, color: Colors.white),
                          ),
                          subtitle: Text(
                            "HW: PKR ${hwRev.toStringAsFixed(0)} | USB Media: PKR ${mediaRev.toStringAsFixed(0)}",
                            style: const TextStyle(color: Colors.grey, fontSize: 12),
                          ),
                          trailing: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.end,
                            children: [
                              Text(
                                "PKR ${sale['total_amount']}",
                                style: const TextStyle(fontWeight: FontWeight.bold, color: Color(0xFF10B981), fontSize: 15),
                              ),
                              Text(
                                "Profit: PKR ${sale['total_profit']}",
                                style: const TextStyle(color: Colors.grey, fontSize: 11),
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
          ],
        ),
      ),
    );
  }

  Widget _buildMetricCard(String title, String value, Color color, IconData icon) {
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFF1E293B),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withOpacity(0.3)),
      ),
      child: Row(
        children: [
          Icon(icon, color: color, size: 26),
          const SizedBox(width: 12),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(title, style: const TextStyle(color: Colors.grey, fontSize: 12)),
              const SizedBox(height: 2),
              Text(value, style: const TextStyle(color: Colors.white, fontSize: 17, fontWeight: FontWeight.bold)),
            ],
          )
        ],
      ),
    );
  }
}
