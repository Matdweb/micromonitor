# ---------- Frontend Dockerfile ----------
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package.json and lockfile
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy rest of the project files
COPY . .

# Expose port (Vite default)
EXPOSE 5173

# Run Vite in dev mode
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
