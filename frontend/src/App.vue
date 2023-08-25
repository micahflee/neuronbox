<template>
    <div class="vh-100 d-flex flex-column">
        <header class="header bg-dark d-flex align-items-center p-4">
            <router-link to="/" class="text-white me-5">NeuronBox</router-link>

            <button class="btn btn-primary btn-sm">
                <router-link to="/transcribe" class="text-white text-decoration-none">Transcribe Audio</router-link>
            </button>
        </header>
        <div class="main-content w-100 d-flex justify-content-center align-items-center flex-grow-1">
            <router-view></router-view>
        </div>
    </div>
</template>

<script setup>
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
</style>
