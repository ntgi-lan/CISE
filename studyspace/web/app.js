"use strict";

/**
 * StudySpace front-end.
 *
 * The browser never decides whether a booking is valid: it asks the server and
 * renders the server's answer. That keeps the JSON API the single source of
 * truth for the booking rules (SPEC engineering issue 2).
 *
 * The identity in the top bar is a convenience, not authentication: it is kept
 * in localStorage and only prefills the booking form and filters "my bookings".
 * A password-based login is listed as a known limitation.
 */

const STORAGE_KEY = "studyspace.identity";

const state = {
  date: "",
  start: "",
  end: "",
  rooms: [],
  bookings: [],
  selectedRoom: null,
  identity: null,
};

const elements = {
  searchForm: document.getElementById("search-form"),
  date: document.getElementById("search-date"),
  start: document.getElementById("search-start"),
  end: document.getElementById("search-end"),
  capacity: document.getElementById("search-capacity"),
  building: document.getElementById("search-building"),
  searchStatus: document.getElementById("search-status"),
  results: document.getElementById("room-results"),
  mySection: document.getElementById("my-section"),
  myDate: document.getElementById("my-date"),
  myStatus: document.getElementById("my-status"),
  myList: document.getElementById("my-list"),
  bookingsDate: document.getElementById("bookings-date"),
  bookingsStatus: document.getElementById("bookings-status"),
  bookingList: document.getElementById("booking-list"),
  staffPanel: document.getElementById("staff-panel"),
  staffStats: document.getElementById("staff-stats"),
  staffTable: document.getElementById("staff-table"),
  identityLabel: document.getElementById("identity-label"),
  identityButton: document.getElementById("identity-button"),
  identitySignout: document.getElementById("identity-signout"),
  identityDialog: document.getElementById("identity-dialog"),
  identityForm: document.getElementById("identity-form"),
  identityName: document.getElementById("identity-name"),
  identityEmail: document.getElementById("identity-email"),
  identityCancel: document.getElementById("identity-cancel"),
  roomDialog: document.getElementById("room-dialog"),
  roomTitle: document.getElementById("room-title"),
  roomDetails: document.getElementById("room-details"),
  roomClose: document.getElementById("room-close"),
  roomBook: document.getElementById("room-book"),
  dialog: document.getElementById("booking-dialog"),
  dialogRoomName: document.getElementById("dialog-room-name"),
  dialogSlot: document.getElementById("dialog-slot"),
  bookingForm: document.getElementById("booking-form"),
  bookingName: document.getElementById("booking-name"),
  bookingEmail: document.getElementById("booking-email"),
  dialogError: document.getElementById("dialog-error"),
  dialogCancel: document.getElementById("dialog-cancel"),
};

function localDateString(date) {
  const pad = (value) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

function tomorrow() {
  const date = new Date();
  date.setDate(date.getDate() + 1);
  return date;
}

function toIso(date, time) {
  return `${date}T${time}:00`;
}

function setStatus(element, message, isError = false) {
  element.textContent = message;
  element.classList.toggle("error", isError);
}

async function requestJson(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (response.status === 204) {
    return null;
  }
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = payload.error || {};
    throw new Error(error.message || `Request failed with status ${response.status}.`);
  }
  return payload;
}

// ---------------------------------------------------------------- identity

function loadIdentity() {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    state.identity = raw ? JSON.parse(raw) : null;
  } catch (error) {
    state.identity = null;
  }
  renderIdentity();
}

function saveIdentity(name, email) {
  state.identity = { name, email };
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(state.identity));
  } catch (error) {
    /* storage can be unavailable; the session still works in memory */
  }
  renderIdentity();
}

function clearIdentity() {
  state.identity = null;
  try {
    window.localStorage.removeItem(STORAGE_KEY);
  } catch (error) {
    /* ignore */
  }
  renderIdentity();
  renderMyBookings();
}

function renderIdentity() {
  const signedIn = Boolean(state.identity);
  elements.identityLabel.textContent = signedIn
    ? `${state.identity.name} · ${state.identity.email}`
    : "Not signed in";
  elements.identityButton.hidden = signedIn;
  elements.identitySignout.hidden = !signedIn;
  elements.mySection.hidden = !signedIn;
  if (signedIn) {
    elements.myDate.textContent = state.date || "the selected date";
  }
}

function openIdentityDialog() {
  if (state.identity) {
    elements.identityName.value = state.identity.name;
    elements.identityEmail.value = state.identity.email;
  }
  elements.identityDialog.showModal();
  elements.identityName.focus();
}

function submitIdentity() {
  const name = elements.identityName.value.trim();
  const email = elements.identityEmail.value.trim();
  if (!name || !email) {
    return;
  }
  saveIdentity(name, email);
  elements.identityDialog.close();
  renderMyBookings();
}

// ---------------------------------------------------------------- rooms

function renderRooms(rooms) {
  elements.results.replaceChildren();
  if (!rooms.length) {
    elements.results.textContent = "No free rooms match this search.";
    return;
  }
  for (const room of rooms) {
    const card = document.createElement("article");
    card.className = "room-card";

    const title = document.createElement("h3");
    title.textContent = room.name;

    const details = document.createElement("p");
    details.textContent = `${room.building} building · capacity ${room.capacity}`;

    const features = document.createElement("p");
    features.className = "muted";
    if (room.features.length) {
      for (const feature of room.features) {
        const chip = document.createElement("span");
        chip.className = "chip";
        chip.textContent = feature;
        features.append(chip);
      }
    } else {
      features.textContent = "No listed features";
    }

    const actions = document.createElement("div");
    actions.className = "card-actions";

    const bookButton = document.createElement("button");
    bookButton.type = "button";
    bookButton.textContent = "Book";
    bookButton.addEventListener("click", () => openBookingDialog(room));

    const detailButton = document.createElement("button");
    detailButton.type = "button";
    detailButton.className = "ghost-button";
    detailButton.textContent = "Details";
    detailButton.addEventListener("click", () => openRoomDialog(room));

    actions.append(bookButton, detailButton);
    card.append(title, details, features, actions);
    elements.results.append(card);
  }
}

function openRoomDialog(room) {
  state.selectedRoom = room;
  elements.roomTitle.textContent = room.name;
  elements.roomDetails.replaceChildren();
  const rows = [
    ["Building", room.building],
    ["Capacity", String(room.capacity)],
    ["Features", room.features.length ? room.features.join(", ") : "None listed"],
    ["Window", `${state.date}, ${state.start}–${state.end}`],
  ];
  for (const [term, value] of rows) {
    const dt = document.createElement("dt");
    dt.textContent = term;
    const dd = document.createElement("dd");
    dd.textContent = value;
    elements.roomDetails.append(dt, dd);
  }
  elements.roomDialog.showModal();
}

// ---------------------------------------------------------------- bookings

function bookingRow(booking, options = {}) {
  const item = document.createElement("li");
  const label = document.createElement("span");
  label.textContent =
    `${booking.start.slice(11, 16)}–${booking.end.slice(11, 16)} · ` +
    `${booking.room_id} · ${booking.name}`;
  const cancelButton = document.createElement("button");
  cancelButton.type = "button";
  cancelButton.className = "ghost-button";
  cancelButton.textContent = "Cancel";
  cancelButton.addEventListener("click", () => cancelBooking(booking));
  item.append(label, cancelButton);
  return item;
}

function renderBookings(bookings) {
  elements.bookingList.replaceChildren();
  if (!bookings.length) {
    elements.bookingList.textContent = "No bookings for this date yet.";
    return;
  }
  const list = document.createElement("ul");
  list.className = "booking-list";
  for (const booking of bookings) {
    list.append(bookingRow(booking));
  }
  elements.bookingList.append(list);
}

function renderMyBookings() {
  if (!state.identity) {
    elements.myList.replaceChildren();
    return;
  }
  elements.myDate.textContent = state.date;
  const mine = state.bookings.filter(
    (booking) =>
      booking.email.toLowerCase() === state.identity.email.toLowerCase()
  );
  elements.myList.replaceChildren();
  if (!mine.length) {
    elements.myList.textContent = "You have no bookings for this date.";
    return;
  }
  const list = document.createElement("ul");
  list.className = "booking-list";
  for (const booking of mine) {
    list.append(bookingRow(booking));
  }
  elements.myList.append(list);
}

function statCard(label, value, hint) {
  const card = document.createElement("div");
  card.className = "stat-card";
  const strong = document.createElement("strong");
  strong.textContent = value;
  const span = document.createElement("span");
  span.textContent = label;
  const small = document.createElement("small");
  small.textContent = hint;
  card.append(strong, span, small);
  return card;
}

function renderStaff(bookings) {
  const rooms = new Set(bookings.map((booking) => booking.room_id));
  const hours = bookings.reduce((total, booking) => {
    const start = new Date(booking.start).getTime();
    const end = new Date(booking.end).getTime();
    return total + Math.max(0, end - start) / 3600000;
  }, 0);
  const capacityHours = 10 * 14; // ten rooms, 08:00-22:00
  const utilisation = Math.round((hours / capacityHours) * 100);

  elements.staffStats.replaceChildren(
    statCard("bookings", String(bookings.length), `on ${state.date}`),
    statCard("rooms in use", String(rooms.size), "of 10 seeded rooms"),
    statCard("booked hours", hours.toFixed(1), "sum of all windows"),
    statCard("utilisation", `${utilisation}%`, "of 10 rooms × 14 hours")
  );

  elements.staffTable.replaceChildren();
  if (!bookings.length) {
    elements.staffTable.textContent = "No bookings to show for this date.";
    return;
  }
  const table = document.createElement("table");
  table.className = "data-table";
  const head = document.createElement("thead");
  const headRow = document.createElement("tr");
  for (const label of ["Time", "Room", "Name", "Email", ""]) {
    const th = document.createElement("th");
    th.textContent = label;
    headRow.append(th);
  }
  head.append(headRow);
  const body = document.createElement("tbody");
  for (const booking of bookings) {
    const row = document.createElement("tr");
    for (const value of [
      `${booking.start.slice(11, 16)}–${booking.end.slice(11, 16)}`,
      booking.room_id,
      booking.name,
      booking.email,
    ]) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }
    const actionCell = document.createElement("td");
    const cancelButton = document.createElement("button");
    cancelButton.type = "button";
    cancelButton.className = "ghost-button";
    cancelButton.textContent = "Cancel";
    cancelButton.addEventListener("click", () => cancelBooking(booking));
    actionCell.append(cancelButton);
    row.append(actionCell);
    body.append(row);
  }
  table.append(head, body);
  elements.staffTable.append(table);
}

async function loadBookings() {
  if (!state.date) {
    return;
  }
  elements.bookingsDate.textContent = state.date;
  elements.myDate.textContent = state.date;
  try {
    const payload = await requestJson(
      `/api/bookings?date=${encodeURIComponent(state.date)}`
    );
    state.bookings = payload.bookings;
    renderBookings(payload.bookings);
    renderMyBookings();
    renderStaff(payload.bookings);
    setStatus(elements.bookingsStatus, "");
  } catch (error) {
    setStatus(elements.bookingsStatus, error.message, true);
  }
}

async function cancelBooking(booking) {
  const confirmed = window.confirm(
    `Cancel the booking for ${booking.name} at ${booking.start.slice(11, 16)}?`
  );
  if (!confirmed) {
    return;
  }
  try {
    await requestJson(`/api/bookings/${booking.id}`, { method: "DELETE" });
    await search();
  } catch (error) {
    setStatus(elements.bookingsStatus, error.message, true);
  }
}

async function search() {
  const date = elements.date.value;
  const start = elements.start.value;
  const end = elements.end.value;
  const capacity = Number(elements.capacity.value);

  if (!date || !start || !end) {
    setStatus(elements.searchStatus, "Choose a date and a start and end time.", true);
    return;
  }
  if (end <= start) {
    setStatus(elements.searchStatus, "The end time must be after the start time.", true);
    return;
  }

  state.date = date;
  state.start = start;
  state.end = end;
  elements.myDate.textContent = date;
  setStatus(elements.searchStatus, "Searching…");
  try {
    const query = new URLSearchParams({
      start: toIso(date, start),
      end: toIso(date, end),
      min_capacity: String(capacity),
    });
    if (elements.building.value) {
      query.set("building", elements.building.value);
    }
    const payload = await requestJson(`/api/rooms?${query.toString()}`);
    state.rooms = payload.rooms;
    setStatus(
      elements.searchStatus,
      `${payload.count} room${payload.count === 1 ? "" : "s"} free for this window.`
    );
    renderRooms(payload.rooms);
    await loadBookings();
  } catch (error) {
    setStatus(elements.searchStatus, error.message, true);
  }
}

function openBookingDialog(room) {
  state.selectedRoom = room;
  elements.dialogRoomName.textContent = room.name;
  elements.dialogSlot.textContent = `${state.date}, ${state.start}–${state.end}`;
  elements.dialogError.textContent = "";
  if (state.identity) {
    elements.bookingName.value = state.identity.name;
    elements.bookingEmail.value = state.identity.email;
  }
  elements.dialog.showModal();
  elements.bookingName.focus();
}

function closeBookingDialog() {
  elements.dialog.close();
  elements.dialogError.textContent = "";
}

async function submitBooking() {
  if (!state.selectedRoom) {
    return;
  }
  elements.dialogError.textContent = "";
  try {
    await requestJson("/api/bookings", {
      method: "POST",
      body: JSON.stringify({
        room_id: state.selectedRoom.id,
        name: elements.bookingName.value.trim(),
        email: elements.bookingEmail.value.trim(),
        start: toIso(state.date, state.start),
        end: toIso(state.date, state.end),
      }),
    });
    closeBookingDialog();
    await search();
  } catch (error) {
    setStatus(elements.dialogError, error.message, true);
  }
}

elements.searchForm.addEventListener("submit", (event) => {
  event.preventDefault();
  search();
});

elements.identityButton.addEventListener("click", openIdentityDialog);
elements.identitySignout.addEventListener("click", clearIdentity);
elements.identityCancel.addEventListener("click", () => elements.identityDialog.close());
elements.identityForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitIdentity();
});

elements.roomClose.addEventListener("click", () => elements.roomDialog.close());
elements.roomBook.addEventListener("click", () => {
  elements.roomDialog.close();
  if (state.selectedRoom) {
    openBookingDialog(state.selectedRoom);
  }
});

elements.dialogCancel.addEventListener("click", closeBookingDialog);
elements.bookingForm.addEventListener("submit", (event) => {
  event.preventDefault();
  submitBooking();
});

function initialise() {
  loadIdentity();
  elements.date.value = localDateString(tomorrow());
  search();
}

document.addEventListener("DOMContentLoaded", initialise);
