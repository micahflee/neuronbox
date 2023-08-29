<template>
    <div class="container">
        <h1 class="mb-4">Models</h1>
        <p class="mb-4">
            All of my smarts come from open source AI models. These models can get big so I'm not packaged with them. Since
            I operate entirely on your computer, you'll need to download the models that you want to use.
        </p>

        <div class="card mb-4">
            <div class="card-header">Transcribe Audio</div>
            <div class="card-body">
                <p>
                    I transcribe audio using OpenAI's open source neural network called <a
                        href="https://openai.com/research/whisper" target="_blank">Whisper</a>.
                    You have a choice of using different sized models
                    (<a href="https://github.com/openai/whisper/blob/main/model-card.md" target="_blank">learn more</a>
                    about the differences between these models). The larger models require significantly more disk space and
                    RAM compared to the smaller models.
                </p>
            </div>

            <template v-for="model in models.transcribe" :key="model.name">
                <Model :site="site" :table="table" :itemId="itemId" :field="field" :featureName="transcribe" :model="model"
                    @refresh-models="refreshModels">
                </Model>
            </template>
        </div>

        <div class="card mb-4">
            <div class="card-header">Translate Text</div>
            <div class="card-body">
                <p>
                    I translate text using <a href="https://huggingface.co/Helsinki-NLP">NLP models</a> created at the <a
                        herf="https://blogs.helsinki.fi/language-technology/" target="_blank">University of Helsinki</a>.
                    You'll need to download a different model for each language you're interested in translating from. (So
                    far, I'm only supporting translating to English, but that shouldn't be hard to change in the future.)
                </p>
            </div>

            <template v-for="model in models.translate" :key="model.name">
                <Model :site="site" :table="table" :itemId="itemId" :field="field" :featureName="transcribe" :model="model"
                    @refresh-models="refreshModels">
                </Model>
            </template>
        </div>
    </div>
</template>
  
<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { invoke } from '@tauri-apps/api/tauri';

import Model from "../components/Model.vue";
import { API_URL } from '../config';

const features = ref([
    { name: "transcribe", description: "Transcribe Audio" },
    { name: "translate", description: "Translate Text" }
]);
const models = ref([]);

async function refreshModels() {
    try {
        const response = await axios.get(`${API_URL}/models`);
        models.value = response.data.models;
    } catch (error) {
        invoke('message_dialog', {
            title: 'Error fetching models',
            message: error.message,
            kind: 'error'
        });
        console.error("Error fetching models:", error);
    }
}

onMounted(async () => {
    await refreshModels();
});

</script>
  
<style scoped></style>
