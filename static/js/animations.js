// GSAP Animations and Interactions

document.addEventListener('DOMContentLoaded', () => {
    // Initial Reveal
    gsap.from("header", {
        y: -50,
        opacity: 0,
        duration: 1.2,
        ease: "power4.out"
    });

    gsap.from(".glass", {
        scale: 0.9,
        opacity: 0,
        duration: 1,
        stagger: 0.1,
        ease: "power3.out",
        delay: 0.5
    });
});

const revealAnalysis = () => {
    const tl = gsap.timeline();
    
    tl.to("#dashboard-content", {
        opacity: 0.5,
        scale: 0.98,
        duration: 0.3
    })
    .to("#dashboard-content", {
        opacity: 1,
        scale: 1,
        duration: 0.5,
        ease: "back.out(1.7)"
    });

    gsap.from("#trade-call-card", {
        x: 100,
        opacity: 0,
        duration: 0.8,
        ease: "power2.out"
    });
};

// Exporting functions if needed, or just keeping them global for simplicity in this vanilla setup
window.revealAnalysis = revealAnalysis;
