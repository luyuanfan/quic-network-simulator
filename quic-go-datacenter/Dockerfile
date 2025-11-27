FROM martenseemann/quic-network-simulator-endpoint:latest

RUN apt-get update && \
    apt-get install -y wget tar git ca-certificates && \
    rm -rf /var/lib/apt/lists/*

# need specifically go 1.18.10 for quic-go
RUN wget https://go.dev/dl/go1.18.10.linux-amd64.tar.gz && \
    tar -C /usr/local -xzf go1.18.10.linux-amd64.tar.gz && \
    rm go1.18.10.linux-amd64.tar.gz

ENV PATH="/usr/local/go/bin:${PATH}"
ENV GO111MODULE=on

# download and build your QUIC implementation
WORKDIR /quic-go-scheduler
RUN git clone https://github.com/Nianqing-Gao/quic-go_scheduler.git . && \
    cd example/datacenter_client && \
    go build -o /usr/local/bin/datacenter_client && \
    cd ../datacenter_server && \
    go build -o /usr/local/bin/datacenter_server


# copy run script and run it
COPY run_endpoint.sh .
RUN chmod +x run_endpoint.sh
ENTRYPOINT [ "./run_endpoint.sh" ]