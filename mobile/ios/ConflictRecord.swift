import Foundation

struct ConflictRecord: Identifiable, Codable {
    let conflictId: String
    let assetId: String
    let field: String
    let localValue: String
    let serverValue: String
    let updatedAt: String

    var id: String { conflictId }

    enum CodingKeys: String, CodingKey {
        case conflictId = "id"
        case assetId = "asset_id"
        case field
        case localValue = "local_value"
        case serverValue = "server_value"
        case updatedAt = "updated_at"
    }

    init(
        conflictId: String,
        assetId: String,
        field: String,
        localValue: String,
        serverValue: String,
        updatedAt: String
    ) {
        self.conflictId = conflictId
        self.assetId = assetId
        self.field = field
        self.localValue = localValue
        self.serverValue = serverValue
        self.updatedAt = updatedAt
    }

    init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        let assetId = try container.decodeIfPresent(String.self, forKey: .assetId) ?? ""
        let field = try container.decodeIfPresent(String.self, forKey: .field) ?? ""
        let localValue = try container.decodeIfPresent(String.self, forKey: .localValue) ?? ""
        let serverValue = try container.decodeIfPresent(String.self, forKey: .serverValue) ?? ""
        let updatedAt = try container.decodeIfPresent(String.self, forKey: .updatedAt) ?? ""
        let conflictId = try container.decodeIfPresent(String.self, forKey: .conflictId)
            ?? "\(assetId):\(field)"

        self.init(
            conflictId: conflictId,
            assetId: assetId,
            field: field,
            localValue: localValue,
            serverValue: serverValue,
            updatedAt: updatedAt
        )
    }
}
