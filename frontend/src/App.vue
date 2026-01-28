<!--
SPDX-FileCopyrightText: 2022-present Tobias Kunze
SPDX-License-Identifier: Apache-2.0
-->

<template lang="pug">
.imanage-schedule(:style="{'--scrollparent-width': scrollParentWidth + 'px'}", :class="[draggedSession ? 'is-dragging' : '', displayMode === 'condensed' ? 'condensed-mode' : 'expanded-mode']", @pointerup="stopDragging")
	template(v-if="schedule")
		.schedule-header.no-print
			.schedule-controls-left
				button.mode-toggle-button(@click="toggleDisplayMode", :class="{'active': displayMode === 'condensed'}")
					i.fa(:class="displayMode === 'condensed' ? 'fa-expand' : 'fa-compress'")
					span.mode-label {{ displayMode === 'condensed' ? $t('Expanded View') : $t('Condensed View') }}
			#schedule-action-wrapper-target
		#main-wrapper
			#unassigned.no-print(v-scrollbar.y="", @pointerenter="isUnassigning = true", @pointerleave="isUnassigning = false", :class="{'pinned': unassignedPanelPinned, 'collapse-container': displayMode === 'condensed'}")
				template(v-if="displayMode === 'condensed'")
					h4
						span {{ $t('Unscheduled sessions') }} ({{ unscheduled.length }})
						.controls
							.pin-button(@click.stop="pinUnassignedPanel", :class="{'pinned': unassignedPanelPinned}")
								i.fa.fa-thumb-tack
				template(v-else)
					.title
						bunt-input#filter-input(v-model="unassignedFilterString", :placeholder="translations.filterSessions", icon="search")
						#unassigned-sort(@click="showUnassignedSortMenu = !showUnassignedSortMenu", :class="{'active': showUnassignedSortMenu}")
							i.fa.fa-sort
					#unassigned-sort-menu(v-if="showUnassignedSortMenu")
						.sort-method(v-for="method of unassignedSortMethods", @click="unassignedSort === method.name ? unassignedSortDirection = unassignedSortDirection * -1 : unassignedSort = method.name; showUnassignedSortMenu = false")
							span {{ method.label }}
							i.fa.fa-sort-amount-asc(v-if="unassignedSort === method.name && unassignedSortDirection === 1")
							i.fa.fa-sort-amount-desc(v-if="unassignedSort === method.name && unassignedSortDirection === -1")
				.session-list(:class="{'collapse-content': displayMode === 'condensed'}")
					.new-slot-row
						session.new-break(:session="{title: '+ ' + translations.newBreak, slot_type: 'break'}", :isDragged="false", :displayMode="displayMode", @startDragging="startNewSlot({event: $event.event, slotType: 'break'})", @click="showNewSlotHint('break')", v-tooltip.fixed="{text: newSlotTooltipType === 'break' ? newSlotTooltip : '', show: newSlotTooltipType === 'break' && newSlotTooltip}", @pointerleave="removeNewSlotHint('break')")
						i.fa.fa-question-circle.slot-help-icon(v-tooltip="{text: $t('Breaks are publicly visible on the schedule')}")
					.new-slot-row
						session.new-blocker(:session="{title: '+ ' + translations.newBlocker, slot_type: 'blocker'}", :isDragged="false", :displayMode="displayMode", @startDragging="startNewSlot({event: $event.event, slotType: 'blocker'})", @click="showNewSlotHint('blocker')", v-tooltip.fixed="{text: newSlotTooltipType === 'blocker' ? newSlotTooltip : '', show: newSlotTooltipType === 'blocker' && newSlotTooltip}", @pointerleave="removeNewSlotHint('blocker')")
						i.fa.fa-question-circle.slot-help-icon(v-tooltip="{text: $t('Blockers are for internal planning and will never become public')}")
					session(v-for="un in unscheduled", :session="un", :displayMode="displayMode", @startDragging="startDragging", :isDragged="draggedSession && un.id === draggedSession.id", @click="editorStart(un)")
			#schedule-wrapper(v-scrollbar.x.y="")
				.schedule-controls
					bunt-tabs.days(v-if="days", :modelValue="currentDay.format()", ref="tabs" :class="['grid-tabs']")
						bunt-tab(v-for="day of days", :id="day.format()", :header="day.format(dateFormat)", @selected="changeDay(day)")
				grid-schedule(:sessions="sessions",
					:rooms="schedule.rooms",
					:availabilities="availabilities",
					:warnings="warnings",
					:start="days[0]",
					:end="days.at(-1).clone().endOf('day')",
					:currentDay="currentDay",
					:draggedSession="draggedSession",
					:displayMode="displayMode",
					@changeDay="currentDay = $event",
					@startDragging="startDragging",
					@rescheduleSession="rescheduleSession",
					@createSession="createSession",
					@editSession="editorStart($event)")
			#session-editor-wrapper(v-if="editorSession", @click="editorSession = null")
				form#session-editor(@click.stop="", @submit.prevent="editorSave")
					h3.session-editor-title
						a(v-if="editorSession.code", :href="`/orga/event/${eventSlug}/submissions/${editorSession.code}/`") {{editorSession.title }}
						span(v-else-if="editorSession.title") {{getLocalizedString(editorSession.title) }}
						.btn-sm.btn-secondary.close-button(@click="editorSession = null", role="button")
							i.fa.fa-times
					.data
						template(v-if="editorSession.code && editorSession.speakers && editorSession.speakers.length > 0")
							.data-row.form-group.row
								label.data-label.col-form-label.col-md-3 {{ $t('Speakers') }}
								.col-md-9.data-value
									span(v-for="speaker, index of editorSession.speakers")
										a(:href="`/orga/event/${eventSlug}/speakers/${speaker.code}/`") {{speaker.name}}
										span(v-if="index != editorSession.speakers.length - 1") {{', '}}
							.data-row.form-group.row
								label.data-label.col-form-label.col-md-3 {{ $t('Availabilities') }}
								.col-md-9.data-value
									ul.mt-0.mb-0
										li(v-for="availability of editorSessionAvailabilities") {{ availability }}
						.data-row(v-else).form-group.row
							label.data-label.col-form-label.col-md-3 {{ $t('Title') }}
							.col-md-9
								.i18n-form-group
									template(v-for="locale of locales")
										input(v-model="editorSession.title[locale]", :required="true", :lang="locale", type="text")
						.data-row(v-if="editorSession.slot_type").form-group.row
							label.data-label.col-form-label.col-md-3 {{ $t('Type') }}
							.col-md-9.data-value
								span.slot-type-badge(:class="'slot-type-' + editorSession.slot_type") {{ editorSession.slot_type === 'blocker' ? $t('Blocker') : $t('Break') }}
						.data-row(v-if="editorSession.track").form-group.row
							label.data-label.col-form-label.col-md-3 {{ $t('Track') }}
							.col-md-9.data-value {{ getLocalizedString(editorSession.track.name) }}
						.data-row(v-if="editorSession.room").form-group.row
							label.data-label.col-form-label.col-md-3 {{ $t('Room') }}
							.col-md-9.data-value {{ getLocalizedString(editorSession.room.name) }}
						.data-row.form-control.form-group.row
							label.data-label.col-form-label.col-md-3 {{ $t('Duration') }}
							.col-md-9.number.input-group
								input(v-model="editorSession.duration", type="number", min="1", max="1440", step="1", :required="true")
								.input-group-append
									span.input-group-text {{ $t('minutes') }}

						.data-row(v-if="editorSession.code && warnings[editorSession.code] && warnings[editorSession.code].length").form-group.row
							label.data-label.col-form-label.col-md-3
								i.fa.fa-exclamation-triangle.warning
								span {{ $t('Warnings') }}
							.col-md-9.data-value
								ul(v-if="warnings[editorSession.code].length > 1")
									li.warning(v-for="warning of warnings[editorSession.code]") {{ warning.message }}
								span(v-else) {{ warnings[editorSession.code][0].message }}
					.button-row
						input(type="submit")
						bunt-button.mr-1#btn-delete(v-if="!editorSession.code", @click="editorDelete", :loading="editorSessionWaiting") {{ $t('Delete') }}
						bunt-button.mr-1#btn-unschedule(v-if="editorSession.start && editorSession.room && editorSession.code", @click="editorUnschedule", :loading="editorSessionWaiting") {{ $t('Unschedule') }}
						bunt-button.mr-1#btn-copy-to-rooms(v-if="!editorSession.code && editorSession.start && editorSession.room && editorAvailableRoomsForCopy.length > 0", @click="editorCopyToOtherRooms", :loading="editorSessionWaiting") {{ $t('Copy to other rooms') }}
						bunt-button#btn-save(@click="editorSave", :loading="editorSessionWaiting") {{ $t('Save') }}
	bunt-progress-circular(v-else, size="huge", :page="true")
</template>
<script>
import moment from 'moment-timezone'
import Editor from '~/components/Editor'
import GridSchedule from '~/components/GridSchedule'
import Session from '~/components/Session'
import api from '~/api'
import { getLocalizedString } from '~/utils'

export default {
	name: 'ImanageSchedule',
	components: { Editor, GridSchedule, Session },
	props: {
		locale: String,
		version: {
			type: String,
			default: ''
		}
	},
	data () {
		return {
			moment,
			eventSlug: null,
			scrollParentWidth: Infinity,
			schedule: null,
			availabilities: {rooms: {}, talks: {}},
			warnings: {},
			currentDay: null,
			draggedSession: null,
			editorSession: null,
			editorSessionWaiting: false,
			isUnassigning: false,
			locales: ["en"],
			unassignedFilterString: '',
			unassignedSort: 'title',
			unassignedSortDirection: 1,  // asc
			showUnassignedSortMenu: false,
			newSlotTooltip: '',
			newSlotTooltipType: null,
			displayMode: localStorage.getItem('scheduleDisplayMode') || 'expanded',
			unassignedPanelPinned: false,
			getLocalizedString,
			// i18next-parser doesn't have a pug parser / fails to parse translated
			// strings in attributes (though plain {{}} strings work!), so anything
			// handled in attributes will be collected here instead
			translations: {
				filterSessions: this.$t('Filter sessions'),
				newBreak: this.$t('New break'),
				newBlocker: this.$t('New blocker'),
			}
		}
	},
	computed: {
		roomsLookup () {
			if (!this.schedule) return {}
			return this.schedule.rooms.reduce((acc, room) => { acc[room.id] = room; return acc }, {})
		},
		editorAvailableRoomsForCopy () {
			// Check if we can copy the current break to other rooms
			if (!this.editorSession || this.editorSession.code || !this.editorSession.start || !this.editorSession.room) {
				return []
			}
			// Find all rooms that are free at the break's time
			const breakStart = moment(this.editorSession.start)
			const breakEnd = moment(this.editorSession.end || breakStart.clone().add(this.editorSession.duration, 'minutes'))
			const availableRooms = []

			for (const room of this.schedule.rooms) {
				if (room.id === this.editorSession.room.id || room.id === this.editorSession.room) {
					// Skip the current room
					continue
				}
				// Check if there's any session overlapping with the break time in this room
				const hasOverlap = this.schedule.talks.some(talk => {
					if (!talk.start || !talk.room) return false
					if ((talk.room.id || talk.room) !== room.id) return false
					const talkStart = moment(talk.start)
					const talkEnd = moment(talk.end)
					// Check for time overlap
					return talkStart.isBefore(breakEnd) && talkEnd.isAfter(breakStart)
				})
				if (!hasOverlap) {
					availableRooms.push(room)
				}
			}
			return availableRooms
		},
		tracksLookup () {
			if (!this.schedule) return {}
			return this.schedule.tracks.reduce((acc, t) => { acc[t.id] = t; return acc }, {})
		},
		editorSessionAvailabilities () {
			if (!this.editorSession) return []
			const avails = this.availabilities.talks[this.editorSession.id]
			if (!avails.length) return ["–"]
			return avails.map(a => {
				const start = moment(a.start)
				const end = moment(a.end)
				if (start.isSame(end, 'day')) {
					return `${start.format('L LT')} - ${end.format('LT')}`
				} else {
					return `${start.format('L LT')} - ${end.format('L LT')}`
				}
			})
		},
		unassignedSortMethods () {
			const sortMethods = [
				{label: this.$t('Title'), name: 'title'},
				{label: this.$t('Speakers'), name: 'speakers'},
			]
			if (this.schedule && this.schedule.tracks.length > 1) {
				sortMethods.push({label: this.$t('Track'), name: 'track'})
			}
			sortMethods.push({label: this.$t('Duration'), name: 'duration' })
			return sortMethods
		},
		speakersLookup () {
			if (!this.schedule) return {}
			return this.schedule.speakers.reduce((acc, s) => { acc[s.code] = s; return acc }, {})
		},
		unscheduled () {
			if (!this.schedule) return
			let sessions = []
			for (const session of this.schedule.talks.filter(s => !s.start || !s.room)) {
				sessions.push({
					id: session.id,
					code: session.code,
					title: session.title,
					abstract: session.abstract,
					speakers: session.speakers?.map(s => this.speakersLookup[s]),
					track: this.tracksLookup[session.track],
					duration: session.duration,
					state: session.state,
				})
			}
			if (this.unassignedFilterString.length) {
				sessions = sessions.filter(s => {
					const title = getLocalizedString(s.title)
					const speakers = s.speakers?.map(s => s.name).join(', ') || ''
					return title.toLowerCase().includes(this.unassignedFilterString.toLowerCase()) || speakers.toLowerCase().includes(this.unassignedFilterString.toLowerCase())
				})
			}
			// Sort by this.unassignedSort, this.unassignedSortDirection (1 or -1)
			sessions = sessions.sort((a, b) => {
				if (this.unassignedSort == 'title') {
					return getLocalizedString(a.title).toUpperCase().localeCompare(getLocalizedString(b.title).toUpperCase()) * this.unassignedSortDirection
				} else if (this.unassignedSort == 'speakers') {
					const aSpeakers = a.speakers?.map(s => s.name).join(', ') || ''
					const bSpeakers = b.speakers?.map(s => s.name).join(', ') || ''
					return aSpeakers.toUpperCase().localeCompare(bSpeakers.toUpperCase()) * this.unassignedSortDirection
				} else if (this.unassignedSort == 'track') {
					return getLocalizedString(a.track ? a.track.name : '').toUpperCase().localeCompare(getLocalizedString(b.track? b.track.name : '').toUpperCase()) * this.unassignedSortDirection
				} else if (this.unassignedSort == 'duration') {
					return (a.duration - b.duration) * this.unassignedSortDirection
				}
			})
			return sessions
		},
		sessions () {
			if (!this.schedule) return
			const sessions = []
			for (const session of this.schedule.talks.filter(s => s.start && moment(s.start).isSameOrAfter(this.days[0]) && moment(s.start).isSameOrBefore(this.days.at(-1).clone().endOf('day')))) {
				sessions.push({
					id: session.id,
					code: session.code,
					title: session.title,
					abstract: session.abstract,
					start: moment(session.start),
					end: moment(session.end),
					duration: moment(session.end).diff(session.start, 'm'),
					speakers: session.speakers?.map(s => this.speakersLookup[s]),
					track: this.tracksLookup[session.track],
					state: session.state,
					slot_type: session.slot_type,
					room: this.roomsLookup[session.room]
				})
			}
			sessions.sort((a, b) => a.start.diff(b.start))
			return sessions
		},
		days () {
			if (!this.schedule) return
			const days = [moment(this.schedule.event_start).startOf('day')]
			const lastDay = moment(this.schedule.event_end)
			while (!days.at(-1).isSame(lastDay, 'day')) {
				days.push(days.at(-1).clone().add(1, 'days'))
			}
			return days
		},
		inEventTimezone () {
			if (!this.schedule || !this.schedule.talks) return false
			const example = this.schedule.talks[0].start
			return moment.tz(example, this.userTimezone).format('Z') === moment.tz(example, this.schedule.timezone).format('Z')
		},
		dateFormat () {
			// Defaults to dddd DD. MMMM for: all grid schedules with more than two rooms, and all list schedules with less than five days
			// After that, we start to shorten the date string, hoping to reduce unwanted scroll behaviour
			if ((this.schedule && this.schedule.rooms.length > 2) || !this.days || !this.days.length) return 'dddd DD. MMMM'
			if (this.days && this.days.length <= 5) return 'dddd DD. MMMM'
			if (this.days && this.days.length <= 7) return 'dddd DD. MMM'
			return 'ddd DD. MMM'
		}
	},
	async created () {
		const version = ''
		this.schedule = await this.fetchSchedule()
		// needs to be as early as possible
		this.eventTimezone = this.schedule.timezone
		moment.tz.setDefault(this.eventTimezone)
		this.locales = this.schedule.locales
		this.eventSlug = window.location.pathname.split("/")[3]
		this.currentDay = this.days[0]
		window.setTimeout(this.pollUpdates, 10 * 1000)
		await this.fetchAdditionalScheduleData()
		await new Promise((resolve) => {
			const poll = () => {
				if (this.$el.parentElement || this.$el.getRootNode().host) return resolve()
				setTimeout(poll, 100)
			}
			poll()
		})
	},
	async mounted () {
		// We block until we have either a regular parent or a shadow DOM parent
		window.addEventListener('resize', this.onWindowResize)
		this.onWindowResize()

		// Move the Django-generated action buttons into the Vue header with retry
		const moveActionButtons = () => {
			const actionWrapper = document.getElementById('schedule-action-wrapper')
			const actionTarget = document.getElementById('schedule-action-wrapper-target')
			if (actionWrapper && actionTarget) {
				actionTarget.appendChild(actionWrapper)
				actionWrapper.style.display = 'flex'
				return true
			}
			return false
		}

		// Retry up to 50 times with 100ms delay (5 seconds total)
		let attempts = 0
		const maxAttempts = 50
		const tryMove = () => {
			if (moveActionButtons()) {
				return
			}
			attempts++
			if (attempts < maxAttempts) {
				setTimeout(tryMove, 100)
			}
		}
		this.$nextTick(tryMove)
	},
	destroyed () {
		// TODO destroy observers
	},
	methods: {
		toggleDisplayMode () {
			const newMode = this.displayMode === 'expanded' ? 'condensed' : 'expanded'
			this.displayMode = newMode
			localStorage.setItem('scheduleDisplayMode', newMode)

			// Handle sidebar collapse/expand
			if (newMode === 'condensed') {
				// Collapse sidebar in condensed mode
				const sidebar = document.querySelector('.sidebar')
				if (sidebar && !sidebar.classList.contains('collapsed')) {
					localStorage.removeItem('sidebarVisible')
					document.documentElement.classList.remove('sidebar-expanded')
				}
				// Reset unassigned panel to unpinned
				this.unassignedPanelPinned = false
			}
		},
		pinUnassignedPanel () {
			this.unassignedPanelPinned = !this.unassignedPanelPinned
		},
		changeDay (day) {
			if (day.isSame(this.currentDay)) return
			this.currentDay = moment(day, this.eventTimezone).startOf('day')
			window.location.hash = day.format('YYYY-MM-DD')
		},
		saveTalk (session) {
			api.saveTalk(session).then(response => {
				this.warnings[session.code] = response.warnings
				this.schedule.talks.find(s => s.id === session.id).updated = response.updated
			})
		},
		rescheduleSession (e) {
			const movedSession = this.schedule.talks.find(s => s.id === e.session.id)
			this.stopDragging()
			movedSession.start = e.start
			movedSession.end = e.end
			movedSession.room = e.room.id
			this.saveTalk(movedSession)
		},
		createSession (e) {
			api.createTalk(e.session).then(response => {
				this.warnings[e.session.code] = response.warnings
				const newSession = Object.assign({}, e.session)
				newSession.id = response.id
				this.schedule.talks.push(newSession)
				this.editorStart(newSession)
			})
		},
		editorStart (session) {
			this.editorSession = session
		},
		editorSave () {
			this.editorSessionWaiting = true
			this.editorSession.end = moment(this.editorSession.start).clone().add(this.editorSession.duration, 'm')
			this.saveTalk(this.editorSession)

			const session = this.schedule.talks.find(s => s.id === this.editorSession.id)
			session.end = this.editorSession.end
			if (!session.submission) {
				session.title = this.editorSession.title
			}
			this.editorSessionWaiting = false
			this.editorSession = null
		},
		editorDelete () {
			this.editorSessionWaiting = true
			api.deleteTalk(this.editorSession)
			this.schedule.talks = this.schedule.talks.filter(s => s.id !== this.editorSession.id)
			this.editorSessionWaiting = false
			this.editorSession = null
		},
		editorUnschedule () {
			this.editorSessionWaiting = true
			const session = this.schedule.talks.find(s => s.id === this.editorSession.id)
			session.start = null
			session.end = null
			session.room = null
			this.editorSession.start = null
			this.editorSession.end = null
			this.editorSession.room = null
			this.saveTalk(session)
			this.editorSessionWaiting = false
			this.editorSession = null
		},
		async editorCopyToOtherRooms () {
			// Copy the current break to all available rooms
			this.editorSessionWaiting = true
			const availableRooms = this.editorAvailableRoomsForCopy

			for (const room of availableRooms) {
				const newBreak = {
					title: this.editorSession.title,
					description: this.editorSession.description,
					start: this.editorSession.start,
					end: this.editorSession.end,
					duration: this.editorSession.duration,
					room: room.id
				}

				try {
					const response = await api.createTalk(newBreak)
					// Add the newly created break to the schedule
					const createdBreak = {
						id: response.id,
						title: newBreak.title,
						description: newBreak.description,
						start: newBreak.start,
						end: newBreak.end,
						duration: newBreak.duration,
						room: room.id
					}
					this.schedule.talks.push(createdBreak)
					if (response.warnings) {
						this.warnings[response.id] = response.warnings
					}
				} catch (error) {
					console.error('Failed to create break in room', room, error)
				}
			}

			this.editorSessionWaiting = false
			this.editorSession = null
		},
		showNewSlotHint (slotType) {
			// Users try to click the "+ New Break/Blocker" box instead of dragging it to the schedule
			// so we show a hint on-click
			const messages = {
				break: this.$t('Drag the box to the schedule to create a new break'),
				blocker: this.$t('Drag the box to the schedule to create a new blocker'),
			}
			this.newSlotTooltip = messages[slotType]
			this.newSlotTooltipType = slotType
		},
		removeNewSlotHint (slotType) {
			if (this.newSlotTooltipType === slotType) {
				this.newSlotTooltip = ''
				this.newSlotTooltipType = null
			}
		},
		startNewSlot({event, slotType}) {
			const titles = {
				break: this.$t("New break"),
				blocker: this.$t("New blocker"),
			}
			const title = this.locales.reduce((obj, locale) => {
				obj[locale] = titles[slotType]
				return obj
			}, {})
			this.startDragging({event, session: {title, duration: "5", uncreated: true, slot_type: slotType}})
		},
		startDragging ({event, session}) {
			if (this.availabilities && this.availabilities.talks[session.id] && this.availabilities.talks[session.id].length !== 0) {
				session.availabilities = this.availabilities.talks[session.id]
			}
			// TODO: capture the pointer with setPointerCapture(event)
			// This allows us to call stopDragging() even when the mouse is released
			// outside the browser.
			// https://developer.mozilla.org/en-US/docs/Web/API/Element/setPointerCapture
			this.draggedSession = session
		},
		stopDragging (session) {
			try {
				if (this.isUnassigning && this.draggedSession) {
					if (this.draggedSession.code) {
						const movedSession = this.schedule.talks.find(s => s.id === this.draggedSession.id)
						movedSession.start = null
						movedSession.end = null
						movedSession.room = null
						this.saveTalk(movedSession)
					} else if (this.schedule.talks.find(s => s.id === this.draggedSession.id)) {
						this.schedule.talks = this.schedule.talks.filter(s => s.id !== this.draggedSession.id)
						api.deleteTalk(this.draggedSession)
					}
				}
			} finally {
				this.draggedSession = null
				this.isUnassigning = false
			}
		},
		onWindowResize () {
			this.scrollParentWidth = document.body.offsetWidth
		},
		async fetchSchedule(options) {
		  const schedule = await (api.fetchTalks(options))
		  return schedule
		},
		async fetchAdditionalScheduleData() {
			this.availabilities = await api.fetchAvailabilities()
			this.warnings = await api.fetchWarnings()
		},
		async pollUpdates () {
			this.fetchSchedule({since: this.since, warnings: true}).then(schedule => {
				if (schedule.version !== this.schedule.version) {
					// we need to reload if a new schedule version is available
					window.location.reload()
				}
				// For each talk in the schedule, we check if it has changed and if our update date is newer than the last change
				schedule.talks.forEach(talk => {
					const oldTalk = this.schedule.talks.find(t => t.id === talk.id)
					if (!oldTalk) {
						this.schedule.talks.push(talk)
					} else {
						if (moment(talk.updated).isAfter(moment(oldTalk.updated))) {
							Object.assign(oldTalk, talk)
						}
					}
				})
				this.since = schedule.now
				window.setTimeout(this.pollUpdates, 10 * 1000)
			})
		}
	}
}
</script>
<style lang="stylus">
#page-content
	padding: 0

.imanage-schedule
	display: flex
	flex-direction: column
	min-height: 0
	min-width: 0
	height: calc(100vh - 85px)
	width: 100%
	font-size: 14px
	padding-left: 24px
	font-family: var(--font-family)
	color: var(--color-text)
	background-color: var(--color-bg-app)

	h1, h2, h3, h4, h5, h6, legend, button, .btn
		font-family: var(--font-family-title)

	.bunt-scrollbar-rail-wrapper-y
		display: none

	&.is-dragging
		user-select: none
		cursor: grabbing

	#main-wrapper
		display: flex
		flex: auto
		min-height: 0
		min-width: 0

	.collapse-container
		position: fixed
		bottom: 16px
		right: 16px
		width: 320px
		z-index: 500
		background-color: $clr-white
		padding: 16px
		box-shadow: var(--shadow-lg)
		border-radius: var(--border-radius)
		overflow-y: hidden
		transition: all 0.3s ease

		.collapse-content
			display: none
			overflow-y: auto
			max-height: 400px

		&:hover
			.collapse-content
				display: block

		h4
			margin: 0
			font-size: 16px
			font-weight: 600
			display: flex
			justify-content: space-between
			align-items: center
			color: var(--color-text)

	&.condensed-mode
		#unassigned
			margin-top: 0
			z-index: 501
			font-size: 16px
			background-color: transparent

			.session-list
				margin-right: 0

			&.pinned .collapse-content
				display: block

			.bunt-scrollbar-rail-wrapper-y
				top: 30px

			.pin-button
				padding: 4px
				cursor: pointer
				border-radius: 4px
				transition: background-color 0.2s

				&:hover
					background-color: $clr-grey-100

				&.pinned
					color: var(--color-primary)
					background-color: $clr-grey-100

		#schedule-wrapper
			margin-right: 0

	.settings
		margin-left: 18px
		align-self: flex-start
		display: flex
		align-items: center
		position: sticky
		z-index: 100
		left: 18px

		.bunt-select
			max-width: 300px
			padding-right: 8px

		.timezone-label
			cursor: default
			color: $clr-secondary-text-light

	.days
		tabs-style(active-color: $clr-primary, indicator-color: $clr-primary, background-color: transparent)
		overflow-x: auto
		margin-bottom: 0
		flex: auto
		min-width: 0
		height: 56px

		.bunt-tabs-header
			min-width: min-content
			border-bottom: 1px solid $clr-dividers-light

		.bunt-tabs-header-items
			justify-content: center
			min-width: min-content

			.bunt-tab-header-item
				min-width: min-content
				text-transform: uppercase
				font-weight: 600
				letter-spacing: 0.5px
				color: $clr-secondary-text-light

				&.active
					color: var(--color-primary)

			.bunt-tab-header-item-text
				white-space: nowrap

	#unassigned
		margin-top: 24px
		background-color: $clr-white
		width: 360px
		flex: none
		border-right: 1px solid $clr-dividers-light
		display: flex
		flex-direction: column

		.session-list
			margin-right: 0
			padding: 0 12px

		> .bunt-scrollbar-rail-y
			margin: 0

		> .title
			padding 12px 16px
			font-size: 18px
			font-weight: 600
			background-color: $clr-white
			border-bottom: 1px solid $clr-dividers-light
			display: flex
			align-items: center
			margin-left: 0

			#filter-input
				flex: 1
				margin-right: 8px

				.label-input-container
					background-color: $clr-grey-50
					border-radius: 6px
					padding: 6px 12px

					.outline
						display: none

					input
						font-size: 14px

			#unassigned-sort
				width: 32px
				height: 32px
				display: flex
				align-items: center
				justify-content: center
				cursor: pointer
				border-radius: 6px
				color: $clr-secondary-text-light
				transition: all 0.2s

				&:hover, &.active
					background-color: $clr-grey-100
					color: var(--color-primary)

		.new-slot-row
			display: flex
			align-items: center
			padding: 8px 0

			.slot-help-icon
				margin-left: 8px
				margin-right: 8px
				color: $clr-grey-400
				cursor: help
				font-size: 14px

				&:hover
					color: var(--color-primary)

		.new-break.c-linear-schedule-session, .new-blocker.c-linear-schedule-session
			min-height: 48px
			flex: 1
			margin: 0
			border-radius: var(--border-radius)
			box-shadow: var(--shadow-sm)
			transition: all 0.2s

			&:hover
				box-shadow: var(--shadow-md)
				transform: translateY(-1px)

		#unassigned-sort-menu
			color: var(--color-text)
			display: flex
			flex-direction: column
			background-color: white
			position: absolute
			top: 60px
			right: 16px
			width: 160px
			font-size: 14px
			cursor: pointer
			z-index: 1000
			box-shadow: var(--shadow-lg)
			border-radius: 6px
			text-align: left
			overflow: hidden
			border: 1px solid $clr-dividers-light

			.sort-method
				padding: 10px 16px
				display: flex
				justify-content: space-between
				align-items: center
				transition: background-color 0.2s

				&:hover
					background-color: $clr-grey-50

	.schedule-header
		display: flex
		justify-content: space-between
		align-items: center
		margin: 16px 24px 16px 0
		max-width: 100%
		padding: 0

		.schedule-controls-left
			display: flex
			align-items: center
			gap: 12px

			.mode-toggle-button
				display: flex
				align-items: center
				gap: 8px
				padding: 8px 16px
				background-color: $clr-white
				border: 1px solid $clr-dividers-light
				border-radius: 6px
				cursor: pointer
				font-size: 14px
				font-weight: 500
				color: var(--color-text)
				transition: all 0.2s
				box-shadow: var(--shadow-sm)

				&:hover
					background-color: $clr-grey-50
					border-color: $clr-grey-300
					transform: translateY(-1px)
					box-shadow: var(--shadow-md)

				&.active
					background-color: var(--color-primary)
					color: $clr-white
					border-color: var(--color-primary)

				.fa
					font-size: 16px

		#schedule-action-wrapper-target
			display: flex
			align-items: center

			#schedule-action-wrapper
				display: flex !important
				gap: 8px

				.btn
					border-radius: 6px !important
					font-weight: 500 !important
					padding: 8px 16px !important
					box-shadow: var(--shadow-sm) !important
					transition: all 0.2s !important

					&:hover
						transform: translateY(-1px) !important
						box-shadow: var(--shadow-md) !important

	#schedule-wrapper
		width: 100%
		margin-right: 0
		background-color: $clr-grey-50

	.schedule-controls
		display: flex
		justify-content: space-between
		align-items: center
		position: sticky
		left: 0
		top: 0
		z-index: 30
		background-color: $clr-white
		border-bottom: 1px solid $clr-dividers-light
		box-shadow: var(--shadow-sm)

	#session-editor-wrapper
		position: absolute
		z-index: 1000
		top: 0
		left: 0
		width: 100%
		height: 100%
		background-color: rgba(0, 0, 0, 0.6)
		backdrop-filter: blur(2px)

		#session-editor
			background-color: $clr-white
			border-radius: 12px
			padding: 0
			position: absolute
			top: 50%
			left: 50%
			transform: translate(-50%, -50%)
			width: 680px
			box-shadow: var(--shadow-lg)
			overflow: hidden
			display: flex
			flex-direction: column
			max-height: 90vh

			.session-editor-title
				font-size: 20px
				font-weight: 600
				margin: 0
				padding: 20px 24px
				background-color: $clr-grey-50
				border-bottom: 1px solid $clr-dividers-light
				display: flex
				align-items: center
				justify-content: space-between

				a, span
					color: var(--color-text)
					text-decoration: none
					flex: 1
					ellipsis()

				.close-button
					position: static
					width: 32px
					height: 32px
					display: flex
					align-items: center
					justify-content: center
					background-color: transparent
					color: $clr-grey-500
					border-radius: 6px
					cursor: pointer
					transition: all 0.2s
					margin-left: 16px

					&:hover
						background-color: $clr-grey-200
						color: $clr-danger

			.data
				display: flex
				flex-direction: column
				font-size: 15px
				padding: 24px
				overflow-y: auto
				flex: 1

				.data-row
					margin-bottom: 16px
					align-items: center

					&:last-child
						margin-bottom: 0

					.data-label
						font-weight: 500
						color: $clr-secondary-text-light

					.data-value
						color: var(--color-text)

						ul
							list-style: none
							padding: 0
							margin: 0

							li
								margin-bottom: 4px

					input[type="text"], input[type="number"]
						width: 100%
						padding: 8px 12px
						border: 1px solid $clr-dividers-light
						border-radius: 6px
						font-size: 14px
						transition: border-color 0.2s

						&:focus
							outline: none
							border-color: var(--color-primary)
							box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.1)

				.slot-type-badge
					display: inline-block
					padding: 4px 12px
					border-radius: 20px
					font-weight: 500
					font-size: 13px

					&.slot-type-break
						background-color: $clr-grey-100
						color: $clr-grey-700
						border: 1px solid $clr-grey-200

					&.slot-type-blocker
						background-color: #fef2f2
						color: #ef4444
						border: 1px solid #fee2e2

			.button-row
				display: flex
				width: 100%
				padding: 16px 24px
				background-color: $clr-grey-50
				border-top: 1px solid $clr-dividers-light
				margin-top: 0
				gap: 12px

				.bunt-button-content
					font-size: 14px !important
					font-weight: 500 !important

				button
					height: 38px
					padding: 0 16px
					border-radius: 6px !important
					text-transform: none !important
					box-shadow: var(--shadow-sm) !important
					transition: all 0.2s !important

					&:hover
						transform: translateY(-1px) !important
						box-shadow: var(--shadow-md) !important

				#btn-delete
					button-style(color: $clr-danger, text-color: $clr-white)

				#btn-unschedule
					button-style(color: $clr-warning, text-color: $clr-white)

				#btn-copy-to-rooms
					button-style(color: #3b82f6, text-color: $clr-white)

				#btn-save
					margin-left: auto
					button-style(color: $clr-primary, text-color: $clr-white)

				[type=submit]
					display: none

		.warning
			color: $clr-danger
			display: flex
			align-items: center
			gap: 8px
			background-color: #fef2f2
			padding: 12px
			border-radius: 6px
			border: 1px solid #fee2e2

			i
				font-size: 18px
</style>
