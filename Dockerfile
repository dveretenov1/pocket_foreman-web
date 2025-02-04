FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies (including dev dependencies)
RUN npm install

# Copy source files
COPY . .

# Set environment variables
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=development

# Expose port
EXPOSE 3000

# Start the development server
CMD ["npm", "run", "dev"]
