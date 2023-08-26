<template>
    <div class="container">
        <h1 class="mb-4">Models</h1>
        <p class="mb-4">
            All of my smarts come from open source AI models. These models can get big so I'm not packaged with them. Since
            I operate entirely on your computer, you'll need to download the models that you want to use.
        </p>

        <!-- Transcribe Audio Section -->
        <div class="card mb-4">
            <div class="card-header">Transcribe Audio</div>
            <div class="card-body">
                <p>I transcribe audio using OpenAI's open source neural network called <a
                        href="https://openai.com/research/whisper" @click="openExternalLink">Whisper</a>. You have a choice
                    of using different sized
                    models. The larger models require significantly more disk space and RAM compared to the smaller models.
                </p>

                <div v-for="model in transcribeModels" :key="model.name" class="row mb-3">
                    <div class="col-md-2">
                        <h5>{{ model.name }}</h5>
                    </div>
                    <div class="col-md-6">
                        <p>{{ model.description }}</p>
                    </div>
                    <div class="col-md-2">
                        <p v-if="model.downloaded">Downloaded</p>
                        <p v-else>Not downloaded</p>
                    </div>
                    <div class="col-md-2">
                        <button v-if="model.downloaded" @click="deleteModel(model.name)"
                            class="btn btn-danger">Delete</button>
                        <button v-else @click="downloadModel(model.name)" class="btn btn-primary">Download</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
</template>
  
<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

import { invoke } from '@tauri-apps/api/tauri';

const transcribeModels = ref([]);

onMounted(async () => {
    try {
        const response = await axios.get('http://127.0.0.1:52014/models');
        transcribeModels.value = response.data.models.transcribe;
    } catch (error) {
        console.error("Error fetching models:", error);
    }
});

const deleteModel = async (modelName) => {
    try {
        await axios.post('http://127.0.0.1:52014/models/delete', { model: modelName });
        // Refresh models after deletion
        const response = await axios.get('http://127.0.0.1:52014/models');
        transcribeModels.value = response.data.models.transcribe;
    } catch (error) {
        console.error("Error deleting model:", error);
    }
}

const downloadModel = async (modelName) => {
    try {
        await axios.post('http://127.0.0.1:52014/models/download', { model: modelName });
        // Refresh models after download
        const response = await axios.get('http://127.0.0.1:52014/models');
        transcribeModels.value = response.data.models.transcribe;
    } catch (error) {
        console.error("Error downloading model:", error);
    }
}

function openExternalLink(event) {
    event.preventDefault();
    const url = event.target.href;
    invoke('open', { uri: url });
}
</script>
  
<style scoped></style>
