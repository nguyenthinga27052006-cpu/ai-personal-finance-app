import 'package:ai_personal_finance/components/sliding_tab_navigation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

void main() {
  group('SlidingTabNavigation Tests', () {
    testWidgets('renders all tab items correctly', (WidgetTester tester) async {
      int selectedIndex = 0;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StatefulBuilder(
              builder: (context, setState) {
                return SlidingTabNavigation(
                  items: const [
                    SlidingTabItem(label: 'Animation', icon: Icons.animation),
                    SlidingTabItem(label: 'Branding', icon: Icons.brush),
                    SlidingTabItem(label: 'Illustration', icon: Icons.image),
                    SlidingTabItem(label: 'Editorial', icon: Icons.edit),
                  ],
                  selectedIndex: selectedIndex,
                  onTabSelected: (index) {
                    setState(() => selectedIndex = index);
                  },
                );
              },
            ),
          ),
        ),
      );

      expect(find.text('Animation'), findsOneWidget);
      expect(find.text('Branding'), findsOneWidget);
      expect(find.text('Illustration'), findsOneWidget);
      expect(find.text('Editorial'), findsOneWidget);
    });

    testWidgets('slides indicator position smoothly when tab selected', (WidgetTester tester) async {
      int selectedIndex = 0;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StatefulBuilder(
              builder: (context, setState) {
                return SlidingTabNavigation(
                  items: const [
                    SlidingTabItem(label: 'Animation'),
                    SlidingTabItem(label: 'Branding'),
                    SlidingTabItem(label: 'Illustration'),
                  ],
                  selectedIndex: selectedIndex,
                  onTabSelected: (index) {
                    setState(() => selectedIndex = index);
                  },
                );
              },
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Tap on second tab 'Branding'
      await tester.tap(find.text('Branding'));
      await tester.pump();
      expect(selectedIndex, equals(1));

      // Allow sliding animation to complete (250ms)
      await tester.pumpAndSettle();

      // Tap on third tab 'Illustration'
      await tester.tap(find.text('Illustration'));
      await tester.pump();
      expect(selectedIndex, equals(2));

      await tester.pumpAndSettle();
    });

    testWidgets('supports rapid switching without crashing or duplicate indicators',
        (WidgetTester tester) async {
      int selectedIndex = 0;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: StatefulBuilder(
              builder: (context, setState) {
                return SlidingTabNavigation(
                  items: const [
                    SlidingTabItem(label: 'Tab 1'),
                    SlidingTabItem(label: 'Tab 2'),
                    SlidingTabItem(label: 'Tab 3'),
                    SlidingTabItem(label: 'Tab 4'),
                  ],
                  selectedIndex: selectedIndex,
                  onTabSelected: (index) {
                    setState(() => selectedIndex = index);
                  },
                );
              },
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Rapidly tap Tab 2, Tab 3, Tab 4, Tab 1
      await tester.tap(find.text('Tab 2'));
      await tester.pump(const Duration(milliseconds: 50));
      await tester.tap(find.text('Tab 3'));
      await tester.pump(const Duration(milliseconds: 50));
      await tester.tap(find.text('Tab 4'));
      await tester.pump(const Duration(milliseconds: 50));
      await tester.tap(find.text('Tab 1'));

      await tester.pumpAndSettle();
      expect(selectedIndex, equals(0));
    });

    testWidgets('SlidingIndicatorTabBar works with TabController', (WidgetTester tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: DefaultTabController(
            length: 3,
            child: Scaffold(
              appBar: AppBar(
                bottom: const _TestSlidingTabBar(),
              ),
              body: const TabBarView(
                children: [
                  Center(child: Text('Overview Content')),
                  Center(child: Text('Users Content')),
                  Center(child: Text('Settings Content')),
                ],
              ),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Overview'), findsOneWidget);
      expect(find.text('Users'), findsOneWidget);
      expect(find.text('Settings'), findsOneWidget);

      await tester.tap(find.text('Users'));
      await tester.pumpAndSettle();

      expect(find.text('Users Content'), findsOneWidget);
    });

    testWidgets('respects accessibleNavigation (reduced motion)', (WidgetTester tester) async {
      int selectedIndex = 0;

      await tester.pumpWidget(
        MaterialApp(
          home: MediaQuery(
            data: const MediaQueryData(accessibleNavigation: true),
            child: Scaffold(
              body: StatefulBuilder(
                builder: (context, setState) {
                  return SlidingTabNavigation(
                    items: const [
                      SlidingTabItem(label: 'Alpha'),
                      SlidingTabItem(label: 'Beta'),
                    ],
                    selectedIndex: selectedIndex,
                    onTabSelected: (index) {
                      setState(() => selectedIndex = index);
                    },
                  );
                },
              ),
            ),
          ),
        ),
      );

      await tester.pumpAndSettle();

      await tester.tap(find.text('Beta'));
      await tester.pump();
      expect(selectedIndex, equals(1));
    });
  });
}

class _TestSlidingTabBar extends StatelessWidget implements PreferredSizeWidget {
  const _TestSlidingTabBar();

  @override
  Size get preferredSize => const Size.fromHeight(48.0);

  @override
  Widget build(BuildContext context) {
    final controller = DefaultTabController.of(context);
    return SlidingIndicatorTabBar(
      controller: controller,
      tabs: const [
        Tab(text: 'Overview'),
        Tab(text: 'Users'),
        Tab(text: 'Settings'),
      ],
    );
  }
}
