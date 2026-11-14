import gsap from 'gsap'
import { ScrollTrigger } from 'gsap/ScrollTrigger'

gsap.registerPlugin(ScrollTrigger)

// Fait apparaitre les elements [data-revele] d'une section quand elle arrive a l'ecran.
// Rien ne bouge si l'utilisateur a demande a reduire les animations.
export function useRevele(racine: Ref<HTMLElement | null>) {
  let ctx: gsap.Context | null = null

  onMounted(async () => {
    await nextTick()
    if (!racine.value) return
    ctx = gsap.context(() => {
      gsap.matchMedia().add('(prefers-reduced-motion: no-preference)', () => {
        gsap.from('[data-revele]', {
          opacity: 0,
          y: 30,
          duration: 0.8,
          stagger: 0.1,
          ease: 'power3.out',
          scrollTrigger: { trigger: racine.value, start: 'top 78%' },
        })
      })
    }, racine.value)
  })

  onBeforeUnmount(() => ctx?.revert())
}