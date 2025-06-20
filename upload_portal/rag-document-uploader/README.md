# RAG Document Uploader

This project is a web portal that allows users to upload documents for use in a Retrieval-Augmented Generation (RAG) tool. It is built using React for the frontend and Express.js for the backend, with Tailwind CSS for styling.

## Features

- Upload documents in PDF, TXT, and DOCX formats.
- Drag-and-drop functionality for file uploads.
- Display of uploaded files with their names and sizes.
- Optional description input for each uploaded file.
- Loading indicator during file uploads.
- Error handling for invalid file types and sizes.

## Project Structure

```
rag-document-uploader
├── client                # Frontend application
│   ├── src
│   │   ├── components    # React components
│   │   │   ├── FileUploader.tsx
│   │   │   ├── FileList.tsx
│   │   │   └── LoadingIndicator.tsx
│   │   ├── App.tsx       # Main application component
│   │   ├── index.tsx     # Entry point for React app
│   │   └── styles
│   │       └── index.css  # Global styles
│   ├── public
│   │   └── index.html     # Main HTML template
│   ├── package.json       # Client dependencies and scripts
│   └── tailwind.config.js  # Tailwind CSS configuration
├── server                # Backend application
│   ├── src
│   │   ├── routes
│   │   │   └── upload.ts  # Express route for file uploads
│   │   ├── middleware
│   │   │   └── fileValidation.ts  # File validation middleware
│   │   └── app.ts         # Entry point for Express server
│   ├── uploads            # Directory for storing uploaded files
│   ├── package.json       # Server dependencies and scripts
│   └── tsconfig.json      # TypeScript configuration
└── README.md              # Project documentation
```

## Getting Started

### Prerequisites

- Node.js (version 14 or higher)
- npm or yarn

### Installation

1. Clone the repository:

   ```
   git clone <repository-url>
   cd rag-document-uploader
   ```

2. Install dependencies for the client:

   ```
   cd client
   npm install
   ```

3. Install dependencies for the server:

   ```
   cd server
   npm install
   ```

### Running the Application

1. Start the server:

   ```
   cd server
   npm start
   ```

2. Start the client:

   ```
   cd client
   npm start
   ```

3. Open your browser and navigate to `http://localhost:3000` to access the RAG Document Uploader.

## Usage

- Use the drag-and-drop area or file input to upload documents.
- View the list of uploaded files along with their sizes.
- Provide optional descriptions for each file before submitting.

## License

This project is licensed under the MIT License. See the LICENSE file for details.