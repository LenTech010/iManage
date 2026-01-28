// SPDX-FileCopyrightText: 2025-present Tobias Kunze
// SPDX-License-Identifier: Apache-2.0

import i18next from 'i18next'

// Import translation files
import enTranslations from '../../locales/en/translation.json'

const resources = {
	en: {
		translation: enTranslations
	}
}

export default async function initI18n(locale = 'en') {
	await i18next.init({
		lng: locale || 'en',
		fallbackLng: 'en',
		resources,
		interpolation: {
			escapeValue: false // Vue already escapes values
		}
	})

	// Return a simple i18n plugin for Vue 3
	return {
		install(app) {
			app.config.globalProperties.$t = (key) => i18next.t(key)
			app.config.globalProperties.$i18n = i18next
		}
	}
}
