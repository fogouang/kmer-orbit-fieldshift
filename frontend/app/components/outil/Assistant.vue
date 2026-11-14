<script setup lang="ts">
// Assistant : questions sur les rotations affichees. Le serveur recalcule les resultats,
// le modele ne recoit que les donnees Field Shift et chaque chiffre de sa reponse est verifie.
import type { MessageAssistant } from '~/composables/useFieldShiftApi'
import { messageErreur } from '~/composables/useFieldShiftApi'

const { t } = useI18n()
const api = useFieldShiftApi()
const o = useOutil()

const messages = ref<MessageAssistant[]>([])
const question = ref('')
const attente = ref(false)
const erreur = ref<string | null>(null)
const liste = ref<HTMLElement | null>(null)

const suggestions = computed(() => {
  const s = [t('outil.assistant.suggestions.meilleure'), t('outil.assistant.suggestions.acide')]
  if (o.resultat.value?.actuelle) s.push(t('outil.assistant.suggestions.actuelle'))
  s.push(t('outil.assistant.suggestions.legumineuse'))
  return s
})

// Nouveau resultat (autres priorites, autre langue...) : la conversation repart de zero
watch(() => o.resultat.value, () => {
  messages.value = []
  erreur.value = null
})

async function envoyer(texte?: string) {
  const q = (texte ?? question.value).trim()
  const contexte = o.derniereRequete.value
  if (!q || attente.value || !contexte) return
  erreur.value = null
  const historique = messages.value.slice(-6)
  messages.value.push({ role: 'user', contenu: q })
  question.value = ''
  attente.value = true
  try {
    const r = await api.assistant({ question: q, contexte, historique })
    messages.value.push({ role: 'assistant', contenu: r.reponse })
  } catch (e) {
    messages.value.pop() // la question n'a pas eu de reponse : on la rend a l'utilisateur
    question.value = q
    erreur.value = messageErreur(e)
  } finally {
    attente.value = false
    await nextTick()
    liste.value?.scrollTo({ top: liste.value.scrollHeight, behavior: 'smooth' })
  }
}
</script>

<template>
  <section class="rounded-2xl bg-white border border-trait p-4 md:p-5" :aria-label="t('outil.assistant.titre')">
    <div class="flex items-start gap-3">
      <span class="grid place-items-center size-10 shrink-0 rounded-full bg-primary/10 text-primary">
        <i class="pi pi-comments" aria-hidden="true" />
      </span>
      <div>
        <h2 class="font-bold text-lg text-foret leading-tight">{{ t('outil.assistant.titre') }}</h2>
        <p class="text-sm text-encre-2">{{ t('outil.assistant.intro') }}</p>
      </div>
    </div>

    <!-- Conversation -->
    <div
      v-if="messages.length || attente"
      ref="liste"
      class="mt-4 max-h-96 overflow-y-auto space-y-3 pr-1"
      aria-live="polite"
    >
      <div
        v-for="(m, i) in messages"
        :key="i"
        class="flex"
        :class="m.role === 'user' ? 'justify-end' : 'justify-start'"
      >
        <p
          class="max-w-[85%] rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed whitespace-pre-line"
          :class="m.role === 'user' ? 'bg-primary/10 text-foret rounded-br-sm' : 'bg-brume text-encre rounded-bl-sm'"
        >
          <span class="sr-only">{{ m.role === 'user' ? t('outil.assistant.vous') : t('outil.assistant.assistant') }} : </span>
          {{ m.contenu }}
        </p>
      </div>
      <p v-if="attente" class="flex items-center gap-2 text-sm text-encre-2">
        <i class="pi pi-spin pi-spinner" aria-hidden="true" />
        {{ t('outil.assistant.attente') }}
      </p>
    </div>

    <!-- Questions suggerees -->
    <div v-if="!messages.length" class="mt-4 flex flex-wrap gap-2">
      <button
        v-for="s in suggestions"
        :key="s"
        type="button"
        class="rounded-full border border-primary/30 bg-primary/5 px-3 py-1.5 text-sm text-primary-700 hover:bg-primary/10 disabled:opacity-50"
        :disabled="attente || !o.derniereRequete.value"
        @click="envoyer(s)"
      >
        {{ s }}
      </button>
    </div>

    <Message v-if="erreur" severity="error" class="mt-3">{{ erreur }}</Message>

    <form class="mt-4 flex gap-2" @submit.prevent="envoyer()">
      <label for="question-assistant" class="sr-only">{{ t('outil.assistant.placeholder') }}</label>
      <InputText
        id="question-assistant"
        v-model="question"
        :placeholder="t('outil.assistant.placeholder')"
        maxlength="500"
        class="flex-1 min-w-0"
        :disabled="attente || !o.derniereRequete.value"
      />
      <Button
        type="submit"
        icon="pi pi-send"
        :aria-label="t('outil.assistant.envoyer')"
        :loading="attente"
        :disabled="!question.trim() || !o.derniereRequete.value"
      />
    </form>

    <p class="mt-3 flex gap-2 text-xs text-encre-2 leading-relaxed">
      <i class="pi pi-shield mt-0.5" aria-hidden="true" />
      {{ t('outil.assistant.avertissement') }}
    </p>
  </section>
</template>