<template>
  <v-app>
    <v-app-bar>
      <v-tabs
        align-tabs="start"
      >
        <v-tab
          to="/"
        >
          Search
        </v-tab>
        <v-tab
          v-if="configStore.aboutTabEnabled"
          to="/about"
        >
          About
        </v-tab>
      </v-tabs>
      <v-spacer />
      <v-btn
        icon
        href="https://www.linkedin.com/groups/9243555/"
        target="_blank"
        rel="noopener"
        aria-label="STARS4Water on LinkedIn"
      >
        <v-icon>mdi-linkedin</v-icon>
      </v-btn>
      <v-btn
        icon
        href="mailto:info@stars4water.eu"
        aria-label="Contact STARS4Water"
      >
        <v-icon>mdi-email-outline</v-icon>
      </v-btn>
      <v-btn
        v-if="configStore.authEnabled"
        :loading="isLoading"
        color="primary"
        variant="text"
        @click="handleLogin"
      >
        <v-icon class="me-2">
          mdi-account
        </v-icon>
        Login
      </v-btn>
    </v-app-bar>
    <v-main>
      <slot /> 
    </v-main>
    <DisclaimerDialog />
  </v-app>
</template>

<script setup>

  import { useAuth } from '~/composables/useAuth'
  import { useConfigStore } from '~/stores/config'
  import DisclaimerDialog from '~/components/DisclaimerDialog.vue'

  const { login, isLoading } = useAuth()
  const configStore = useConfigStore()

  const handleLogin = () => {
    login()
  }
</script>
