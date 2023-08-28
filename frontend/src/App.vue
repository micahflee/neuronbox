<template>
    <div class="vh-100 d-flex flex-column">
        <div v-show="isLoading" id="loading" class="d-flex flex-grow-1 align-items-center justify-content-center">
            <div class="d-flex flex-column align-items-center">
                <img src="/assets/loading.gif" alt="Loading..." class="mb-4 loading">
                <p class="mb-4">{{ loadingMessage }}</p>
            </div>
        </div>
        <div v-show="!isLoading">
            <header class="header bg-dark d-flex align-items-center p-4">
                <router-link to="/" class="text-white me-5">NeuronBox</router-link>

                <router-link :to="{ path: '/transcribe' }"
                    class="btn btn-primary btn-sm me-3 text-white text-decoration-none">
                    Transcribe Audio
                </router-link>

                <router-link :to="{ path: '/models' }" class="btn btn-primary btn-sm text-white text-decoration-none">
                    Models
                </router-link>
            </header>
            <div class="main-content w-100 d-flex flex-grow-1">
                <router-view @change-loading="changeLoading"></router-view>
            </div>
        </div>
    </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const isLoading = ref(false);
const loadingMessage = ref('');

const changeLoading = (active, message) => {
    console.log(`changeLoading, active=${active}, message:${message}`);
    isLoading.value = active;
    loadingMessage.value = message;
}

const checkAPIHealth = async () => {
    changeLoading(true, 'Waiting for API to boot');
    try {
        let response = await axios.get('http://127.0.0.1:52014/health');
        if (response.status === 200) {
            changeLoading(false, '');
        } else {
            console.error("API is not ready. Received status:", response.status);
        }
    } catch (error) {
        console.error("Backend is not ready yet, waiting for 1 second...");
        setTimeout(checkAPIHealth, 1000);
    }
};
checkAPIHealth();
</script>

<style>
.header {
    height: 40px;
}

.main-content {
    padding: 2rem;
    overflow-y: auto;
}

a {
    color: #007bff;
}

a:hover {
    color: #0056b3;
    text-decoration: underline;
}

.loading {
    border-radius: 50vw;
}

#loading.d-flex[style*="display: none"] {
    display: none !important;
}
</style>
