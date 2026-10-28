jQuery(document).ready(function($) {
  if ($(".dnxte_testimonial_child").length) {
    $(".dnxte_testimonial_child").addClass("swiper-slide");
    $(".dnxte_testimonial_child .et_pb_module_inner").addClass(
      "dnxte-tstimonial-item"
    );
  }
  $(".dnxte-tstimonial-wrap").length &&
    $(".dnxte-tstimonial-wrap").each(function(e) {
      const testimonialData = $(this).data();
      const testimonialBreakpoints =
        testimonialData.breakpoints && testimonialData.breakpoints.split("|");
      const testimonialSwiper = new Swiper(this, {
        autoplay: {
          enabled: 1 === testimonialData.autoplay,
          delay: testimonialData.delay ? parseInt(testimonialData.delay) : 0,
          disableOnInteraction: !1,
        },
        slidesPerView:
          testimonialBreakpoints && parseFloat(testimonialBreakpoints[0]),
        centeredSlides: "on" === testimonialData.center,
        spaceBetween: parseInt(testimonialData.spacing),
        direction: testimonialData.direction,
        speed: testimonialData.speed ? parseInt(testimonialData.speed) : 400,
        grabCursor: "on" === testimonialData.grab,
        loop: "on" === testimonialData.loop,
        breakpoints: {
          1024: {
            slidesPerView:
              testimonialBreakpoints && parseFloat(testimonialBreakpoints[0]),
          },
          768: {
            slidesPerView:
              testimonialBreakpoints && parseFloat(testimonialBreakpoints[1]),
          },
          479: {
            slidesPerView:
              testimonialBreakpoints && parseFloat(testimonialBreakpoints[2]),
          },
          200: {
            slidesPerView:
              testimonialBreakpoints && parseFloat(testimonialBreakpoints[2]),
          },
        },
        pagination: {
          el: ".swiper-pagination",
          dynamicBullets: "on" === testimonialData.paginationBullets,
          clickable: true,
          type: testimonialData.paginationType,
        },
        navigation: {
          nextEl: $(this).siblings(".swiper-button-next")[0],
          prevEl: $(this).siblings(".swiper-button-prev")[0],
        },
        keyboard: {
          enabled: "on" === testimonialData.keyboard,
          onlyInViewport: false,
        },
        mousewheel: {
          enabled: "on" === testimonialData.mousewheel,
          invert: true,
        },
        observer: !0,
        observeParents: !0,
        observeSlideChildren: !0,
      });

      if (
        1 === testimonialData.autoplay &&
        testimonialData.pauseonhover === 1
      ) {
        $(this).on("mouseenter", function() {
          testimonialSwiper.autoplay.stop();
        });
        $(this).on("mouseleave", function() {
          testimonialSwiper.autoplay.start();
        });
      }
    });
});
