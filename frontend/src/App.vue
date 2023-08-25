<template>
    <div class="vh-100 d-flex flex-row no-padding">
        <aside class="sidebar bg-dark d-flex flex-column align-items-start p-4">
            <router-link to="/" class="text-white mb-5" style="font-size: 2rem; font-weight: bold; text-decoration: none;">
                NeuronBox
            </router-link>

            <button class="btn btn-primary mb-3 w-100">
                <router-link to="/transcribe" class="text-white text-decoration-none">Transcribe Audio</router-link>
            </button>
        </aside>
        <div class="main-content w-100 d-flex justify-content-center align-items-center">
            <router-view></router-view>
        </div>
    </div>
</template>

<script setup>
</script>

<style>
.no-padding {
    padding-left: 0;
    padding-right: 0;
}


.sidebar {
    width: 250px;
    /* Sidebar width */
}

.main-content {
    padding: 2rem;
    overflow-y: auto;
    /* Enable scroll if content overflows */
}

a {
    color: #007bff;
}

a:hover {
    color: #0056b3;
    text-decoration: underline;
}
</style>
