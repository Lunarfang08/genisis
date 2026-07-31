FROM node:22-alpine AS dependencies
WORKDIR /app
COPY package.json package-lock.json ./
COPY apps/web/package.json ./apps/web/package.json
COPY packages/shared-types/package.json ./packages/shared-types/package.json
RUN npm ci --ignore-scripts --no-audit --no-fund

FROM node:22-alpine AS build
WORKDIR /app
ARG NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}
COPY --from=dependencies /app/node_modules ./node_modules
COPY package.json package-lock.json ./
COPY apps/web ./apps/web
COPY packages/shared-types ./packages/shared-types
RUN npm run build:web

FROM node:22-alpine AS runtime
ENV NODE_ENV=production
WORKDIR /app
RUN addgroup --system --gid 1001 genesis \
    && adduser --system --uid 1001 --ingroup genesis genesis
COPY --from=build --chown=genesis:genesis /app ./
USER genesis
EXPOSE 3000
CMD ["npm", "run", "start", "--workspace", "@genesis/web", "--", "--host", "0.0.0.0"]
