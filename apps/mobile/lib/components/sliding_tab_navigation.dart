import 'package:flutter/material.dart';

/// Represents a single tab item in [SlidingTabNavigation].
class SlidingTabItem {
  final String label;
  final IconData? icon;
  final Widget? customWidget;

  const SlidingTabItem({
    required this.label,
    this.icon,
    this.customWidget,
  });
}

/// A modern, responsive navigation & tab bar featuring a smooth sliding line indicator
/// and visual hover feedback, inspired by high-end web transition design.
class SlidingTabNavigation extends StatefulWidget {
  final List<SlidingTabItem> items;
  final int selectedIndex;
  final ValueChanged<int> onTabSelected;
  final Color? activeColor;
  final Color? inactiveColor;
  final Color? hoverColor;
  final Color? indicatorColor;
  final double indicatorHeight;
  final double indicatorPadding;
  final EdgeInsetsGeometry padding;
  final bool isScrollable;
  final Duration animationDuration;
  final Curve animationCurve;

  const SlidingTabNavigation({
    super.key,
    required this.items,
    required this.selectedIndex,
    required this.onTabSelected,
    this.activeColor,
    this.inactiveColor,
    this.hoverColor,
    this.indicatorColor,
    this.indicatorHeight = 3.0,
    this.indicatorPadding = 8.0,
    this.padding = const EdgeInsets.symmetric(horizontal: 12.0, vertical: 8.0),
    this.isScrollable = false,
    this.animationDuration = const Duration(milliseconds: 250),
    this.animationCurve = Curves.easeOut,
  });

  @override
  State<SlidingTabNavigation> createState() => _SlidingTabNavigationState();
}

class _SlidingTabNavigationState extends State<SlidingTabNavigation> {
  final List<GlobalKey> _keys = [];
  int? _hoveredIndex;
  double _indicatorLeft = 0.0;
  double _indicatorWidth = 0.0;
  bool _initialized = false;

  @override
  void initState() {
    super.initState();
    _updateKeys();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _updateIndicatorPosition(animate: false);
    });
  }

  @override
  void didUpdateWidget(SlidingTabNavigation oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.items.length != widget.items.length) {
      _updateKeys();
    }
    if (oldWidget.selectedIndex != widget.selectedIndex ||
        oldWidget.items.length != widget.items.length) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _updateIndicatorPosition(animate: true);
      });
    }
  }

  void _updateKeys() {
    _keys.clear();
    for (int i = 0; i < widget.items.length; i++) {
      _keys.add(GlobalKey());
    }
  }

  void _updateIndicatorPosition({bool animate = true}) {
    if (!mounted || widget.items.isEmpty) return;
    final int safeIndex = widget.selectedIndex.clamp(0, widget.items.length - 1);
    final GlobalKey targetKey = _keys[safeIndex];
    final RenderBox? renderBox = targetKey.currentContext?.findRenderObject() as RenderBox?;
    final RenderBox? parentBox = context.findRenderObject() as RenderBox?;

    if (renderBox != null && parentBox != null) {
      final Offset targetPosition = renderBox.localToGlobal(Offset.zero, ancestor: parentBox);
      final double width = renderBox.size.width;
      final double targetWidth = (width - (widget.indicatorPadding * 2)).clamp(12.0, width);
      final double targetLeft = targetPosition.dx + (width - targetWidth) / 2;

      setState(() {
        _indicatorLeft = targetLeft;
        _indicatorWidth = targetWidth;
        _initialized = true;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    final Color activeColor = widget.activeColor ??
        (isDark ? Colors.tealAccent.shade200 : theme.primaryColor);
    final Color inactiveColor = widget.inactiveColor ??
        theme.textTheme.bodyMedium?.color?.withOpacity(0.65) ??
        Colors.grey.shade600;
    final Color indicatorColor = widget.indicatorColor ?? activeColor;

    final bool isReducedMotion = MediaQuery.of(context).accessibleNavigation;
    final Duration effectiveDuration =
        isReducedMotion ? Duration.zero : widget.animationDuration;

    final List<Widget> tabWidgets = [];

    for (int i = 0; i < widget.items.length; i++) {
      final item = widget.items[i];
      final isSelected = i == widget.selectedIndex;
      final isHovered = i == _hoveredIndex;

      tabWidgets.add(
        MouseRegion(
          key: _keys[i],
          onEnter: (_) => setState(() => _hoveredIndex = i),
          onExit: (_) => setState(() => _hoveredIndex = null),
          cursor: SystemMouseCursors.click,
          child: GestureDetector(
            behavior: HitTestBehavior.opaque,
            onTap: () {
              widget.onTabSelected(i);
              _updateIndicatorPosition(animate: true);
            },
            child: AnimatedContainer(
              duration: effectiveDuration,
              curve: widget.animationCurve,
              padding: widget.padding,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(6.0),
                color: isHovered && !isSelected
                    ? (widget.hoverColor ?? (isDark ? Colors.white10 : Colors.black.withOpacity(0.04)))
                    : Colors.transparent,
              ),
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (item.icon != null) ...[
                    Icon(
                      item.icon,
                      size: 18.0,
                      color: isSelected
                          ? activeColor
                          : (isHovered ? activeColor.withOpacity(0.85) : inactiveColor),
                    ),
                    const SizedBox(width: 8.0),
                  ],
                  if (item.customWidget != null)
                    item.customWidget!
                  else
                    AnimatedDefaultTextStyle(
                      duration: effectiveDuration,
                      curve: widget.animationCurve,
                      style: TextStyle(
                        fontSize: 14.0,
                        fontWeight: isSelected ? FontWeight.w600 : FontWeight.w500,
                        color: isSelected
                            ? activeColor
                            : (isHovered ? activeColor.withOpacity(0.85) : inactiveColor),
                      ),
                      child: Text(item.label),
                    ),
                ],
              ),
            ),
          ),
        ),
      );
    }

    final Widget contentRow = Row(
      mainAxisSize: widget.isScrollable ? MainAxisSize.min : MainAxisSize.max,
      mainAxisAlignment: widget.isScrollable ? MainAxisAlignment.start : MainAxisAlignment.spaceAround,
      children: tabWidgets,
    );

    return SingleChildScrollView(
      scrollDirection: Axis.horizontal,
      physics: widget.isScrollable
          ? const BouncingScrollPhysics()
          : const NeverScrollableScrollPhysics(),
      child: Stack(
        clipBehavior: Clip.none,
        children: [
          contentRow,
          if (_initialized && _indicatorWidth > 0)
            AnimatedPositioned(
              duration: effectiveDuration,
              curve: widget.animationCurve,
              left: _indicatorLeft,
              bottom: 0.0,
              width: _indicatorWidth,
              height: widget.indicatorHeight,
              child: Container(
                decoration: BoxDecoration(
                  color: indicatorColor,
                  borderRadius: BorderRadius.circular(widget.indicatorHeight / 2),
                  boxShadow: [
                    BoxShadow(
                      color: indicatorColor.withOpacity(0.4),
                      blurRadius: 4.0,
                      offset: const Offset(0, 1),
                    ),
                  ],
                ),
              ),
            ),
        ],
      ),
    );
  }
}

/// A customized TabBar wrapper that adds a smooth sliding indicator and hover feedback
/// for screens using standard Flutter [TabController].
class SlidingIndicatorTabBar extends StatelessWidget implements PreferredSizeWidget {
  final TabController controller;
  final List<Widget> tabs;
  final Color? activeColor;
  final Color? inactiveColor;
  final Color? indicatorColor;
  final ValueChanged<int>? onTap;
  final bool isScrollable;

  const SlidingIndicatorTabBar({
    super.key,
    required this.controller,
    required this.tabs,
    this.activeColor,
    this.inactiveColor,
    this.indicatorColor,
    this.onTap,
    this.isScrollable = false,
  });

  @override
  Size get preferredSize => const Size.fromHeight(48.0);

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final List<SlidingTabItem> items = tabs.map((w) {
          if (w is Tab) {
            return SlidingTabItem(
              label: w.text ?? '',
              icon: w.icon != null && w.icon is Icon ? (w.icon as Icon).icon : null,
              customWidget: w.child,
            );
          }
          return SlidingTabItem(label: '', customWidget: w);
        }).toList();

        return SlidingTabNavigation(
          items: items,
          selectedIndex: controller.index,
          onTabSelected: (index) {
            controller.animateTo(index);
            onTap?.call(index);
          },
          activeColor: activeColor,
          inactiveColor: inactiveColor,
          indicatorColor: indicatorColor,
          isScrollable: isScrollable,
        );
      },
    );
  }
}
