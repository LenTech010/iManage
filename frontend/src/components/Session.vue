<!--
SPDX-FileCopyrightText: 2022-present Tobias Kunze
SPDX-License-Identifier: Apache-2.0
-->

<template lang="pug">
.c-linear-schedule-session(:style="style", @pointerdown.stop="$emit('startDragging', {session: session, event: $event})", @dragstart.prevent, :class="classes", draggable="true")
	.time-box
		.start(:class="{'has-ampm': startTime.ampm}", v-if="startTime")
			.time {{ startTime.time }}
			.ampm(v-if="startTime.ampm") {{ startTime.ampm }}
		.duration {{ durationPretty }}
	.info
		.title {{ getLocalizedString(session.title) }}
		.speakers(v-if="session.speakers") {{ session.speakers.map(s => s.name).join(', ') }}
		.pending-line(v-if="session.state && session.state !== 'confirmed' && session.state !== 'accepted'")
			i.fa.fa-exclamation-circle
			span {{ $t('Pending proposal state') }}
		.bottom-info(v-if="!isBreak && !isBlocker")
			.track(v-if="session.track") {{ getLocalizedString(session.track.name) }}
	.warning.no-print(v-if="warnings?.length")
		.warning-icon.text-danger
			span(v-if="warnings.length > 1") {{ warnings.length }}
			i.fa.fa-exclamation-triangle
</template>
<script>
import moment from 'moment-timezone'
import MarkdownIt from 'markdown-it'
import { getLocalizedString } from '~/utils'

const markdownIt = MarkdownIt({
	linkify: true,
	breaks: true
})

export default {
	props: {
		session: Object,
		warnings: Array,
		isDragged: Boolean,
		isDragClone: {
			type: Boolean,
			default: false
		},
		overrideStart: {
			type: Object,
			default: null
		},
		displayMode: {
			type: String,
			default: 'expanded'
		}
	},
	inject: {
		eventUrl: { default: null },
		generateSessionLinkUrl: {
			default () {
				return ({eventUrl, session}) => `${eventUrl}talk/${session.id}/`
			}
		}
	},
	data () {
		return {
			getLocalizedString
		}
	},
	computed: {
		link () {
			return this.generateSessionLinkUrl({eventUrl: this.eventUrl, session: this.session})
		},
		isBreak () {
			return this.session.slot_type === 'break'
		},
		isBlocker () {
			return this.session.slot_type === 'blocker'
		},
		classes () {
			let classes = []
			if (this.isBlocker) classes.push('isblocker')
			else if (this.isBreak) classes.push('isbreak')
			else {
				classes.push('istalk')
				if (this.session.state !== "confirmed" && this.session.state !== "accepted") classes.push('pending')
				else if (this.session.state !== "confirmed") classes.push('unconfirmed')
			}
			if (this.isDragged) classes.push('dragging')
			if (this.isDragClone) classes.push('clone')
			if (this.displayMode === 'condensed') classes.push('condensed')
			return classes
		},
		style () {
			return {
				'--track-color': this.session.track?.color || 'var(--color-primary)'
			}
		},
		startTime () {
			// check if 12h or 24h locale
			const time = this.overrideStart  || this.session.start
			if (!time) return
			if (moment.localeData().longDateFormat('LT').endsWith(' A')) {
				return {
					time: time.format('h:mm'),
					ampm: time.format('A')
				}
			} else {
				return {
					time: moment(time).format('LT')
				}
			}
		},
		durationMinutes () {
			if (!this.session.start) return this.session.duration
			return moment(this.session.end).diff(this.session.start, 'minutes')
		},
		durationPretty () {
			if (!this.durationMinutes) return
			let minutes = this.durationMinutes
			const hours = Math.floor(minutes / 60)
			if (minutes <= 60) {
				return `${minutes}min`
			}
			minutes = minutes % 60
			if (minutes) {
				return `${hours}h${minutes}min`
			}
			return `${hours}h`
		}
	}
}
</script>
<style lang="stylus">
.c-linear-schedule-session
	display: flex
	min-width: 300px
	min-height: 96px
	margin: 8px
	overflow: hidden
	color: $clr-primary-text-light
	position: relative
	cursor: pointer
	user-select: none
	-webkit-user-select: none
	-webkit-user-drag: element
	touch-action: none
	&.clone
		z-index: 200
	&.dragging
		filter: opacity(0.3)
		cursor: inherit
	&.isbreak
		background-color: $clr-grey-200
		border-radius: 6px
		.time-box
			background-color: $clr-grey-500
			.start
				color: $clr-primary-text-dark
			.duration
				color: $clr-secondary-text-dark
		.info
			justify-content: center
			align-items: center
			.title
				font-size: 20px
				color: $clr-secondary-text-light
				text-align: center
	&.isblocker
		background-color: $clr-red-50
		border-radius: 6px
		.time-box
			background-color: $clr-red-200
			.start
				color: $clr-primary-text-dark
			.duration
				color: $clr-secondary-text-dark
		.info
			justify-content: center
			align-items: center
			.title
				font-size: 20px
				color: $clr-red-300
				text-align: center
	&.istalk
		transition: transform 0.2s ease
		.time-box
			background-color: var(--track-color)
			.start
				color: $clr-primary-text-dark
			.duration
				color: $clr-secondary-text-dark
		.info
			border: 1px solid $clr-dividers-light
			border-left: none
			border-radius: 0 var(--border-radius) var(--border-radius) 0
			background-color: $clr-white
			box-shadow: var(--shadow-sm)
			transition: all 0.2s ease
			.title
				font-size: 15px
				font-weight: 600
				margin-bottom: 4px
				color: var(--color-text)
				line-height: 1.4
		&:hover
			z-index: 100
			transform: translateY(-2px)
			.info
				border-color: var(--track-color)
				box-shadow: var(--shadow-md)
				.title
					color: var(--color-primary)
	&.pending, &.unconfirmed
		.time-box
			opacity: 0.5
		.info
			background-image: repeating-linear-gradient(-38deg, $clr-grey-50, $clr-grey-50 10px, $clr-white 10px, $clr-white 20px)
		&:hover
			.info
				border-color: var(--track-color)
				.title
					color: var(--color-primary)
	&.pending
		.info
			border-style: dashed dashed dashed none
	.time-box
		width: 72px
		box-sizing: border-box
		padding: 12px 10px
		border-radius: var(--border-radius) 0 0 var(--border-radius)
		display: flex
		flex-direction: column
		align-items: center
		justify-content: center
		.start
			font-size: 15px
			font-weight: 700
			margin-bottom: 4px
			display: flex
			flex-direction: column
			align-items: center
			line-height: 1.2
			&.has-ampm
				align-self: center
			.ampm
				font-weight: 500
				font-size: 11px
				text-transform: uppercase
				opacity: 0.8
		.duration
			font-size: 12px
			font-weight: 500
			opacity: 0.9
	.info
		flex: auto
		display: flex
		flex-direction: column
		padding: 10px 14px
		min-width: 0
		.title
			font-weight: 600
		.speakers
			color: $clr-secondary-text-light
			font-size: 13px
			margin-bottom: 4px
		.bottom-info
			flex: auto
			display: flex
			align-items: flex-end
			margin-top: 4px
			.track
				flex: 1
				color: var(--track-color)
				font-size: 12px
				font-weight: 600
				text-transform: uppercase
				letter-spacing: 0.5px
				ellipsis()
				margin-right: 4px
	.pending-line
		color: $clr-warning
		.fa
			margin-right: 4px
	.warning
		position: absolute
		top: 0
		right: 0
		padding: 4px 4px
		margin: 4px
		color: #b23e65
		font-size: 16px
		.warning-icon span
			padding-right: 4px
	// Condensed mode styles
	&.condensed
		min-width: 0
		min-height: 60px
		margin: 4px
		&.istalk
			flex-direction: column
			.time-box
				display: none
			.info
				border-radius: 6px
				border-left: 4px solid var(--track-color)
				padding: 4px 6px
				.title
					font-size: 13px
					margin-bottom: 2px
					line-height: 1.3
					overflow: hidden
					text-overflow: ellipsis
				.speakers
					font-size: 11px
					line-height: 1.2
					overflow: hidden
					text-overflow: ellipsis
					white-space: nowrap
				.bottom-info
					display: none
				.pending-line
					font-size: 11px
		&.isbreak
			min-height: 40px
			margin: 4px
			.time-box
				display: none
			.info
				padding: 4px 8px
				.title
					font-size: 14px
		&.isblocker
			min-height: 40px
			margin: 4px
			.time-box
				display: none
			.info
				padding: 4px 8px
				.title
					font-size: 14px
@media print
	.c-linear-schedule-session.isbreak
		border: 2px solid $clr-grey-300 !important
	.c-linear-schedule-session.isblocker
		border: 2px solid $clr-red-200 !important
	.c-linear-schedule-session.istalk .time-box
		border: 2px solid var(--track-color) !important
	.c-linear-schedule-session.istalk .info
		border-right: 2px solid var(--track-color) !important
		border-top: 2px solid var(--track-color) !important
		border-bottom: 2px solid var(--track-color) !important
</style>
