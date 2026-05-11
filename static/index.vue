<template id="page-lndhub">
  <div class="row q-col-gutter-md">
    <div class="col-12 col-md-8 col-lg-7 q-gutter-y-md">
      <div class="row q-gutter-x-md">
        <q-card
          v-for="type in ['invoice', 'admin']"
          :key="type"
          class="q-pa-sm col-12 col-sm"
        >
          <q-card-section class="q-pa-none">
            <div class="text-center">
              <span class="text-capitalize" v-text="type"></span>
              <lnbits-qrcode
                :value="selectedWallet[type]"
                :options="{width: 350}"
                class="rounded-borders"
              ></lnbits-qrcode>
            </div>
            <div class="row q-mt-lg items-center justify-center">
              <q-btn
                outline
                color="grey"
                @click="copyText(selectedWallet[type])"
                class="text-center q-mb-md"
              >
                Copy LndHub <span v-text="type"></span> URL
              </q-btn>
            </div>
          </q-card-section>
        </q-card>
      </div>

      <q-card class="q-pa-lg q-pt-xl lnbits__dialog-card">
        <q-form class="q-gutter-md">
          <q-select
            filled
            dense
            v-model="selectedWallet"
            :options="wallets"
            label="Select wallet:"
          ></q-select>
        </q-form>
      </q-card>
    </div>

    <div class="col-12 col-md-4 col-lg-5 q-gutter-y-md">
      <q-card>
        <q-card-section>
          <h6 class="text-subtitle1 q-my-none">
            {{ g.settings.siteTitle }} LndHub extension
          </h6>
        </q-card-section>
        <q-card-section class="q-pa-none">
          <q-separator></q-separator>
          <q-list>
            <q-expansion-item
              group="extras"
              icon="info"
              label="Instructions"
              default-opened
            >
              <q-card>
                <q-card-section>
                  To access an LNbits wallet from a mobile phone,
                  <ol>
                    <li>
                      Install either
                      <a class="text-secondary" href="https://zeusln.app"
                        >Zeus</a
                      >
                      or
                      <a class="text-secondary" href="https://bluewallet.io/"
                        >BlueWallet</a
                      >;
                    </li>
                    <li>
                      Go to <code>Add a wallet / Import wallet</code> on
                      BlueWallet or <code>Settings / Add a new node</code> on
                      Zeus.
                    </li>
                    <li>Select the desired wallet on this page;</li>
                    <li>
                      Scan one of the two QR codes from the mobile wallet.
                    </li>
                  </ol>
                  <ul>
                    <li>
                      <em>Invoice</em> URLs mean the mobile wallet will only
                      have the authorization to read your payments and invoices
                      and generate new invoices.
                    </li>
                    <li>
                      <em>Admin</em> URLs mean the mobile wallet will be able to
                      pay invoices..
                    </li>
                  </ul>
                </q-card-section>
                <q-btn
                  flat
                  label="Swagger API"
                  type="a"
                  href="../docs#/lndhub"
                ></q-btn>
              </q-card>
            </q-expansion-item>
            <q-separator></q-separator>
            <q-expansion-item group="extras" icon="info" label="LndHub info">
              <q-card>
                <q-card-section>
                  <p>
                    LndHub is a protocol invented by
                    <a class="text-secondary" href="https://bluewallet.io/"
                      >BlueWallet</a
                    >
                    that allows mobile wallets to query payments and balances,
                    generate invoices and make payments from accounts that exist
                    on a server. The protocol is a collection of HTTP endpoints
                    exposed through the internet.
                  </p>
                  <p>
                    For a wallet that supports it, reading a QR code that
                    contains the URL along with secret access credentials should
                    enable access. Currently it is supported by
                    <a class="text-secondary" href="https://zeusln.app">Zeus</a>
                    and
                    <a class="text-secondary" href="https://bluewallet.io/"
                      >BlueWallet</a
                    >.
                  </p>
                </q-card-section>
              </q-card>
            </q-expansion-item>
          </q-list>
        </q-card-section>
      </q-card>
    </div>
  </div>
</template>
