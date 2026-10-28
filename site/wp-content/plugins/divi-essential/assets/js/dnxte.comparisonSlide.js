jQuery(document).ready(function($) {

  // The Divi 5 Visual Builder renders this module with React, which owns the
  // container node and reconciles it on every re-render. twentytwenty() calls
  // container.wrap(), re-parenting that node, so React's next update throws
  // "NotFoundError: Failed to execute 'insertBefore'" and the error boundary
  // replaces the module with "This content could not be displayed".
  //
  // React-rendered sliders are driven by the module's own edit component, so
  // they must be left alone here. Server-rendered markup (front end, and the
  // Divi 4 builder) has no React fiber attached and still initializes normally.
  function isReactManaged(el) {
    return !!el && Object.keys(el).some(function (key) {
      return 0 === key.indexOf('__reactFiber$') || 0 === key.indexOf('__reactInternalInstance$');
    });
  }

  // Initialize a single Before/After slider from its data-* settings.
  function initSlider($el) {
    if (isReactManaged($el[0])) {
      return;
    }

    $el.twentytwenty({
      default_offset_pct: $el.data('offset'), // How much of the before image is visible when the page loads
      orientation: $el.data('orientation'), // Orientation of the before and after images ('horizontal' or 'vertical')
      before_label: $el.data('before-label') ?? '', // Set a custom before label
      after_label: $el.data('after-label') ?? '', // Set a custom after label
      no_overlay: $el.data('overlay') === 'on' ? false : true, //Do not show the overlay with before and after
      move_slider_on_hover: $el.data('move-hover') == 'on' ? true : false, // Move slider on mouse hover?
      move_with_handle_only: $el.data('move-handle') == 'on' ? true : false, // Allow a user to swipe anywhere on the image to control slider movement.
      click_to_move: $el.data('move-click') == 'on' ? true : false,  // Allow a user to click (or tap) anywhere on the image to move the slider to that location.
    });
  }

  // Before After Slider
  $(".dnxte_before_after_wrapper").length && $(".dnxte_before_after_wrapper").each(function () {
    initSlider($(this));
  });

  // Mega Menu mobile panels are a runtime CLONE of the desktop nav: the slider
  // markup is copied but its JS instance (resize/move closures) is not, and the
  // clone was wrapped by twentytwenty while hidden (display:none) so it is frozen
  // at height 0 and renders empty. When a mobile panel opens, reset the cloned
  // markup back to a bare container and build a fresh instance against the now-
  // visible element. A flag prevents re-initializing (and resetting the handle
  // position) every time the panel is reopened.
  document.addEventListener('dnxte-mega-menu:panel-open', function (e) {
    var panel = e.target;
    if (!panel || typeof panel.closest !== 'function' || !panel.closest('.et_mobile_menu')) {
      return; // only the cloned mobile menu has dead, hidden-measured sliders
    }
    $(panel).find('.dnxte_before_after_wrapper').each(function () {
      var $c = $(this);
      if ($c.data('dnxteMobileReinit')) {
        return;
      }
      // Undo what twentytwenty did to the cloned markup, then re-init clean.
      $c.find('.twentytwenty-overlay, .twentytwenty-handle').remove();
      $c.removeClass('twentytwenty-container').css('height', '');
      $c.find('img').removeClass('twentytwenty-before twentytwenty-after').css('clip', '');
      if ($c.parent().hasClass('twentytwenty-wrapper')) {
        $c.unwrap();
      }
      initSlider($c);
      $c.data('dnxteMobileReinit', true);
    });
  });
});
