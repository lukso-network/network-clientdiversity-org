FROM ruby:3.4.0-preview1-alpine3.20

WORKDIR /app

ENV BUNDLE_PATH=/app/vendor/bundle
ENV BUNDLER_VERSION='2.2.23'

RUN apk update && \
  apk upgrade && \
  apk add --no-cache jq build-base curl bash && \
  gem install bundler -v $BUNDLER_VERSION

RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    truncate -s 0 /var/log/*log

RUN bundle config set --local path 'vendor/bundle'
COPY Gemfile Gemfile.lock /app/

RUN bundle install

USER root

COPY . /app

RUN echo $GEM_PATH
RUN $GEM_PATH

