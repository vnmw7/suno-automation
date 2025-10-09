### Project: Song Sidebar Implementation

**Objective:** Architect and implement a sidebar component within the frontend application. This sidebar will list all available songs fetched from the backend, providing users with quick and easy access to navigate between them.

---

### **1. Understand Phase: Analysis of the Existing System**

Before planning the implementation, a thorough analysis of the current codebase is required to ensure the new feature integrates seamlessly with the existing architecture and conventions.

*   **Framework and Architecture:**
    *   The frontend is built with **Remix**, a full-stack web framework for React. This is evident from the file-based routing in `frontend/app/routes/` and the use of `loader` functions for server-side data fetching.
    *   The architecture separates UI components (`frontend/app/components/`), routes (`frontend/app/routes/`), and server-side logic (API routes like `api.list-songs.ts`).

*   **Routing and Layout:**
    *   The main application layout is defined in `frontend/app/root.tsx`, which includes the `<html>`, `<head>`, and `<body>` structure, and renders the active route via the `<Outlet />` component.
    *   The application has a login page (`_index.tsx`) that redirects to `/main` upon successful authentication.
    *   The `/main` route (`main.tsx`) is currently dedicated to displaying "Bible Books," not songs. This indicates that a new route should be created for the song-related features.

*   **Data Fetching:**
    *   Data is fetched on the server side using `loader` functions within the route files.
    *   There is an existing API route at `frontend/app/routes/api.list-songs.ts` that reads the `public/songs` directory and returns a list of MP3 files. This is the endpoint that the new sidebar will use to get the list of songs.

*   **Styling:**
    *   The project uses **Tailwind CSS** for styling, as indicated by the presence of `tailwind.config.ts` and `tailwind.css`. All new components should be styled using Tailwind classes to maintain consistency.

*   **Component Structure:**
    *   Reusable components are located in `frontend/app/components/`. The existing `SidebarFilters.tsx` component can serve as a structural and stylistic reference for the new `SongSidebar` component.

---

### **2. Plan Phase: Detailed Task Breakdown**

Based on the analysis, here is a step-by-step plan to implement the song sidebar.

*   **Task 1: Create a New Route for the Songs Page**
    *   **Action:** Create a new file at `frontend/app/routes/songs.tsx`.
    *   **Rationale:** To avoid mixing the song functionality with the existing bible book functionality in `main.tsx`, a dedicated route for songs is necessary. This promotes separation of concerns.

*   **Task 2: Implement Data Fetching for the Songs Page**
    *   **Action:** Within `songs.tsx`, create a `loader` function that fetches data from the `/api/list-songs` endpoint.
    *   **Rationale:** This follows the established data-fetching pattern in the Remix application. The `loader` will ensure that the list of songs is available on the server before the page is rendered.

*   **Task 3: Create the `SongSidebar` Component**
    *   **Action:** Create a new file at `frontend/app/components/SongSidebar.tsx`.
    *   **Action:** This component will accept a list of song names as a prop and render them as a navigable list.
    *   **Rationale:** Creating a separate, reusable component for the sidebar is a core principle of component-based architecture. It encapsulates the sidebar's logic and presentation.

*   **Task 4: Develop the Main View for the Songs Page**
    *   **Action:** In `songs.tsx`, create the main component that will be rendered on the page.
    *   **Action:** This component will use the `useLoaderData` hook to access the list of songs fetched by the `loader`.
    *   **Action:** It will manage the application state, such as which song is currently selected.

*   **Task 5: Integrate the Sidebar and Main View**
    *   **Action:** Modify the `songs.tsx` component to render the `SongSidebar` and the main content area in a side-by-side layout.
    *   **Action:** Pass the list of songs to the `SongSidebar` component as a prop.
    *   **Rationale:** This step composes the final page from the individual components, creating the desired user interface.

*   **Task 6: Implement Navigation and State Management**
    *   **Action:** Use the `useState` hook in `songs.tsx` to manage the currently selected song.
    *   **Action:** When a song is clicked in the `SongSidebar`, it will update the state in the parent `songs.tsx` component.
    *   **Action:** The main content area will then re-render to display information about the selected song.
    *   **Rationale:** This creates an interactive experience where the user's actions in the sidebar are reflected in the main content area.
