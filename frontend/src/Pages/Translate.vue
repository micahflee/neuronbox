<template>
    <div class="container">
        <div v-if="!translationResult">
            <h1 class="mb-4">Translate Text</h1>
            <p class="mb-4">Enter text in the source language to translate it to English.</p>

            <form @submit.prevent="translateText">
                <div class="row">
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label for="sourceLanguage" class="form-label">Source Language:</label>
                            <select id="sourceLanguage" v-model="formData.sourceLanguage" class="form-select">
                                <option v-for="(languageName, languageCode) in languageCodes" :key="languageCode"
                                    :value="languageCode">
                                    {{ languageName }}
                                </option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label for="sourceText" class="form-label">Source Text:</label>
                            <textarea id="sourceText" v-model="formData.sourceText" class="form-control" rows="4"
                                style="height: 100%;"></textarea>
                        </div>
                        <button type="submit" class="btn btn-primary" :disabled="isTranslateDisabled">Translate</button>
                    </div>
                    <div class="col-md-6">
                        <div class="mb-3">
                            <label class="form-label">English Translation:</label>
                            <textarea class="form-control" :value="translationResult" rows="4" readonly
                                style="height: 100%;"></textarea>
                        </div>
                    </div>
                </div>
            </form>
        </div>
        <div v-if="translationResult">
            <h1 class="mb-4">Translation Results</h1>
            <p class="small text-muted">
                Source Language: {{ languageCodes[formData.sourceLanguage] }}<br />
                Time elapsed: {{ formattedTimeElapsed }}
            </p>
            <p>{{ translationResult }}</p>
        </div>
    </div>
</template>

<script setup>
import { ref, computed, onMounted, defineEmits } from 'vue';
import axios from 'axios';

import { API_URL } from '../config';

const emit = defineEmits(['start-loading', 'stop-loading']);

const translationResult = ref(null);
const translationTimeElapsed = ref(null);

const formattedTimeElapsed = computed(() => {
    const minutes = Math.floor(translationTimeElapsed.value / 60);
    const seconds = Math.round(translationTimeElapsed.value % 60);
    return `${minutes} minute(s) and ${seconds} second(s)`;
});

const formData = ref({
    sourceLanguage: 'es',
    sourceText: '',
});

const languageCodes = ref({});

onMounted(async function () {
    try {
        const response = await axios.get(`${API_URL}/languages`);
        // Filter out the 'en' (English) language code
        const filteredLanguageCodes = Object.entries(response.data).filter(([code, _]) => code !== 'en');
        languageCodes.value = Object.fromEntries(filteredLanguageCodes);
    } catch (error) {
        console.error("Failed to load language codes:", error);
    }
});

const isTranslateDisabled = computed(() => !formData.value.sourceText);

async function translateText() {
    console.log("emitting change-loading true");
    emit('change-loading', true, "I'm thinking about how to translate this 🤔. It might take a few moments...");

    try {
        const response = await axios.post(`${API_URL}/translate`, formData.value, { timeout: 1200000 });

        if (!response.data.success) {
            // Handle error message here
            // You can use invoke('message_dialog') to show error message
        } else {
            translationResult.value = response.data.result;
            translationTimeElapsed.value = response.data.time_elapsed;
        }
    } catch (error) {
        // Handle error here
        console.error("There was an issue translating the text:", error);
    } finally {
        console.log("emitting change-loading false");
        emit('change-loading', false, '');
    }
}
</script>

<style scoped></style>
