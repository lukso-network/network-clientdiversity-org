FROM ruby:3.3-alpine3.20

WORKDIR /app

ENV BUNDLE_PATH=/app/vendor/bundle
ENV BUNDLER_VERSION='2.5.14'

COPY . /app

RUN apk update && \
  apk upgrade && \
  apk add --no-cache jq build-base curl bash && \
  gem install bundler -v $BUNDLER_VERSION

RUN rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    truncate -s 0 /var/log/*log

RUN bundle config set --local path 'vendor/bundle'
RUN bundle install

EXPOSE 4000

ENTRYPOINT ["bundle"]
CMD ["exec", "jekyll", "serve"]

