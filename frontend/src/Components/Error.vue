<template>
    <div class="modal fade" tabindex="-1" aria-hidden="true">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Error</h5>
                    <button type="button" class="btn-close" @click="closeModal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    {{ message }}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" @click="closeModal">Close</button>
                </div>
            </div>
        </div>
    </div>
</template>
  
<script setup>
import { ref, defineProps, watchEffect } from 'vue';

const showError = ref(false);

let errorModal;
const setModalRef = (el) => {
    errorModal = el;
};

watchEffect(() => {
    if (showError.value && errorModal) {
        errorModal.showModal();
    }
});

const props = defineProps(['message']);

const closeModal = () => {
    const modal = new bootstrap.Modal(props.$el);
    modal.hide();
    emit('close');
};

const showModal = () => {
    const modal = new bootstrap.Modal(props.$el);
    modal.show();
};

</script>
