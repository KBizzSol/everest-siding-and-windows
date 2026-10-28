jQuery(document).ready(function($) {
	if ($(".dnxte_logo_carousel_child").length) {
	    $(".dnxte_logo_carousel_child").addClass("swiper-slide");
	    $(".dnxte_logo_carousel_child .et_pb_module_inner").addClass(
	      "dnext-logo-carosuel-item"
	    );
  	}

	$(".dnext-logo-carosuel-active").each(function(e) {
      const logoData = $(this).data();
      const carouselBreakpoint =
        logoData.breakpoints && logoData.breakpoints.split("|");

      const logoSwiper = new Swiper(this, {
        direction: logoData.direction,
        speed: logoData.speed ? parseInt(logoData.speed) : 400,
        spaceBetween: parseInt(logoData.spacing),
        grabCursor: "on" === logoData.grab,
        preventClicksPropagation: true,
        autoplay: {
          enabled: 1 === logoData.autoplay,
          delay: "on" === logoData.smoothscrolling ? 0 : (logoData.delay ? parseInt(logoData.delay) : 0),
          disableOnInteraction: !1,
        },
        slidesPerView: carouselBreakpoint && parseInt(carouselBreakpoint[0]),
        centeredSlides: "on" === logoData.center,
        loop: "on" === logoData.loop,
        breakpoints: {
          1024: {
            slidesPerView:
              carouselBreakpoint && parseInt(carouselBreakpoint[0]),
          },
          768: {
            slidesPerView:
              carouselBreakpoint && parseInt(carouselBreakpoint[1]),
          },
          479: {
            slidesPerView:
              carouselBreakpoint && parseInt(carouselBreakpoint[2]),
          },
          200: {
            slidesPerView:
              carouselBreakpoint && parseInt(carouselBreakpoint[2]),
          },
        },
        pagination: {
          el: ".swiper-pagination",
          dynamicBullets: "on" === logoData.paginationBullets,
          clickable: true,
          type: logoData.paginationType,
        },
        keyboard: {
          enabled: "on" === logoData.keyboard,
          onlyInViewport: false,
        },
        mousewheel: {
          enabled: "on" === logoData.mouse,
          invert: true,
        },
        navigation: {
          nextEl: $(this).siblings(".swiper-button-next")[0],
          prevEl: $(this).siblings(".swiper-button-prev")[0],
        },
        observer: !0,
        observeParents: !0,
        observeSlideChildren: !0,
      });

      if (1 === logoData.autoplay && logoData.pauseonhover === 1) {
        $(this).on("mouseenter", function() {
          logoSwiper.autoplay.stop();
        });
        $(this).on("mouseleave", function() {
          logoSwiper.autoplay.start();
        });
      }
  });
});